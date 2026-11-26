#!/usr/bin/env python3
"""Check only implemented health routes; no credentials, faults or paid APIs."""
import argparse
import json
import sys
import urllib.error
import urllib.request
from uuid import UUID


def check(url, expected_status, timeout):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status, data = response.status, json.load(response)
    except urllib.error.HTTPError as error:
        status, data = error.code, json.load(error)
    if status != expected_status:
        raise ValueError(f'expected HTTP {expected_status}, got {status}')
    if status == 200:
        if data != {'status': 'UP'}:
            raise ValueError('unexpected health body')
    else:
        if set(data) != {'code', 'message', 'retryable', 'correlationId'}:
            raise ValueError('invalid unavailable error envelope')
        UUID(data['correlationId'])
        if data['code'] not in ('DATABASE_NOT_CONFIGURED', 'DATABASE_UNAVAILABLE'):
            raise ValueError('unexpected readiness error code')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--order-base-url', default='http://127.0.0.1:8081')
    parser.add_argument('--analysis-base-url', default='http://127.0.0.1:8001')
    parser.add_argument('--timeout', type=float, default=5)
    parser.add_argument('--expect-order-unready', action='store_true',
                        help='Explicitly expect HTTP 503 when DB is absent; does not certify readiness.')
    args = parser.parse_args()
    if not 0 < args.timeout <= 60:
        parser.error('--timeout must be greater than zero and at most 60 seconds')
    failed = False
    for name, base, ready in [('order', args.order_base_url, 503 if args.expect_order_unready else 200),
                              ('analysis', args.analysis_base_url, 200)]:
        for route, status in [('/health/live', 200), ('/health/ready', ready)]:
            try:
                check(base.rstrip('/') + route, status, args.timeout)
                print(f'PASS {name} {route}: HTTP {status} as expected')
            except (OSError, ValueError) as error:
                # Do not print response bodies, URLs or driver messages.
                print(f'FAIL {name} {route}: {type(error).__name__}', file=sys.stderr)
                failed = True
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
