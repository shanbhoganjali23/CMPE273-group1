#!/usr/bin/env python3
"""Verify local service images with disposable PostgreSQL; no shared stack required."""
import argparse
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from uuid import uuid4, UUID

POSTGRES_IMAGE = 'postgres:16-bookworm@sha256:cd0e9518bda5f2ea667ff84d22795d089720c883f288e215d97ce57437e8ef37'


def docker(*args, env=None, timeout=120):
    result = subprocess.run(['docker', *args], env=env, capture_output=True,
                            text=True, timeout=timeout)
    if result.returncode:
        # Docker diagnostics may contain environment values. Do not print them.
        raise RuntimeError(f'Docker {args[0]} failed; inspect Docker locally')
    return result.stdout.strip()


def wait_for(url, status, code=None, deadline_seconds=45):
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        try:
            try:
                with urllib.request.urlopen(url, timeout=4) as response:
                    actual, data = response.status, json.load(response)
            except urllib.error.HTTPError as error:
                actual, data = error.code, json.load(error)
            if actual == status:
                if status == 200 and data == {'status': 'UP'}:
                    return
                if status == 503 and data.get('code') == code:
                    if set(data) != {'code', 'message', 'retryable', 'correlationId'} or data['retryable'] is not True:
                        raise ValueError('Invalid unavailable error envelope')
                    UUID(data['correlationId'])
                    return
        except (OSError, ValueError):
            pass
        time.sleep(.25)
    raise RuntimeError(f'Health check deadline exceeded (expected HTTP {status})')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--order-image', default='agentmesh-order:dev')
    parser.add_argument('--analysis-image', default='agentmesh-analysis:dev')
    args = parser.parse_args()
    containers = []
    network = None
    failed = False
    try:
        endpoint = os.environ.get('DOCKER_HOST') or docker(
            'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}')
        if not endpoint.startswith(('unix://', 'npipe://')):
            raise RuntimeError('Only a local Docker engine is supported')
        # Verify application images exist before creating any test resources.
        docker('image', 'inspect', args.order_image, args.analysis_image)
        run_id = 'agentmesh-check-' + uuid4().hex[:12]
        network = docker('network', 'create', '--label', 'agentmesh.verification=' + run_id, run_id)
        env = os.environ.copy()
        password = secrets.token_urlsafe(24)
        env.update(POSTGRES_USER='agentmesh_test', POSTGRES_DB='agentmesh_test',
                   POSTGRES_PASSWORD=password, ORDER_DATABASE_PASSWORD=password)

        def start(suffix, image, extra=(), settings=None):
            name = run_id + '-' + suffix
            command = ['run', '-d', '--name', name, '--network', network,
                       '--label', 'agentmesh.verification=' + run_id, *extra, image]
            container_id = docker(*command, env=settings or env, timeout=240)
            containers.append(container_id)
            return container_id

        db = start('postgres', POSTGRES_IMAGE, (
            '--network-alias', 'verification-db', '--tmpfs', '/var/lib/postgresql/data',
            '--env', 'POSTGRES_USER', '--env', 'POSTGRES_DB', '--env', 'POSTGRES_PASSWORD'))
        deadline = time.monotonic() + 45
        while True:
            try:
                docker('exec', db, 'pg_isready', '-U', 'agentmesh_test', '-d', 'agentmesh_test', timeout=5)
                break
            except RuntimeError:
                if time.monotonic() >= deadline:
                    raise RuntimeError('PostgreSQL startup deadline exceeded')
                time.sleep(.25)

        def base(container, port):
            binding = docker('port', container, str(port) + '/tcp')
            return 'http://' + binding

        analysis = start('analysis', args.analysis_image, ('-p', '127.0.0.1::8001'))
        analysis_url = base(analysis, 8001)
        order_settings = (
            '-p', '127.0.0.1::8081', '--env', 'ORDER_DATABASE_ENABLED=true',
            '--env', 'ORDER_DATABASE_URL=jdbc:postgresql://verification-db:5432/agentmesh_test',
            '--env', 'ORDER_DATABASE_USER=agentmesh_test', '--env', 'ORDER_DATABASE_PASSWORD')
        order = start('order', args.order_image, order_settings)
        order_url = base(order, 8081)
        for name, url in [('Order', order_url), ('Analysis', analysis_url)]:
            for path in ['/health/live', '/health/ready']:
                wait_for(url + path, 200)
            print(f'PASS {name} container liveness/readiness HTTP 200', flush=True)

        wrong = env.copy()
        wrong['ORDER_DATABASE_PASSWORD'] = secrets.token_urlsafe(24)
        bad_order = start('bad-password', args.order_image, order_settings, wrong)
        bad_url = base(bad_order, 8081)
        wait_for(bad_url + '/health/live', 200)
        wait_for(bad_url + '/health/ready', 503, 'DATABASE_UNAVAILABLE')
        print('PASS bad database password: live 200, ready 503', flush=True)

        docker('restart', '--time', '5', order)
        # Docker may assign a different ephemeral host port after a restart.
        order_url = base(order, 8081)
        wait_for(order_url + '/health/ready', 200)
        print('PASS Order restart reconnects to database', flush=True)

        docker('stop', '--time', '5', db)
        wait_for(order_url + '/health/ready', 503, 'DATABASE_UNAVAILABLE')
        wait_for(order_url + '/health/live', 200)
        wait_for(analysis_url + '/health/ready', 200)
        print('PASS database loss: Order live 200/ready 503; Analysis ready 200', flush=True)

        docker('start', db)
        wait_for(order_url + '/health/ready', 200)
        print('PASS database return restores Order readiness', flush=True)
        count = docker('exec', db, 'psql', '-U', 'agentmesh_test', '-d', 'agentmesh_test',
                       '-tAc', "SELECT count(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')")
        if count != '0':
            raise RuntimeError('Skeleton unexpectedly created application tables')
        print('PASS no application tables created', flush=True)
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f'FAIL {error}', file=sys.stderr, flush=True)
        failed = True
    finally:
        for container in reversed(containers):
            try:
                docker('rm', '-f', '-v', container, timeout=30)
            except (RuntimeError, OSError, subprocess.TimeoutExpired):
                print('FAIL cleanup: verification container remains; inspect Docker locally', file=sys.stderr)
                failed = True
        if network:
            try:
                docker('network', 'rm', network, timeout=30)
            except (RuntimeError, OSError, subprocess.TimeoutExpired):
                print('FAIL cleanup: verification network remains; inspect Docker locally', file=sys.stderr)
                failed = True
        if containers and not failed:
            print('PASS disposable containers and network removed', flush=True)
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
