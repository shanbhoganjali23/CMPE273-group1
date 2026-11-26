import json
from urllib.parse import unquote
from pathlib import Path

import pytest
import yaml
from openapi_spec_validator import validate

from conftest import CONTRACTS, read

APIS = sorted(CONTRACTS.glob('*-api.yaml'))


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


@pytest.mark.parametrize('path', APIS, ids=lambda p: p.name)
def test_openapi(path):
    validate(yaml.safe_load(path.read_text()), base_uri=path.as_uri())


def test_all_local_references_resolve():
    for path in [*APIS, *CONTRACTS.glob('*.schema.json')]:
        for node in walk(yaml.safe_load(path.read_text())):
            if '$ref' not in node:
                continue
            filename, _, fragment = node['$ref'].partition('#')
            assert '://' not in filename, 'Contract references must resolve offline'
            target = (path.parent / filename).resolve() if filename else path
            assert target.is_relative_to(CONTRACTS)
            value = yaml.safe_load(target.read_text())
            for token in fragment.split('/')[1:]:
                value = value[unquote(token).replace('~1', '/').replace('~0', '~')]


def test_shared_errors_and_mutation_keys():
    assert len(APIS) == 6
    for path in APIS:
        api = read(path.name)
        for route, methods in api['paths'].items():
            for method, operation in methods.items():
                if route.startswith('/health'):
                    continue
                for status in ['400', '401', '403', '404', '409', '422', '502', '503', '504']:
                    assert operation['responses'][status]['content']['application/json']['schema'] == {'$ref': 'error.schema.json'}
                if method in ('post', 'put'):
                    assert any(p['name'] == 'Idempotency-Key' and p['required'] for p in operation['parameters'])
                assert {'traceparent', 'tracestate'} <= {p['name'] for p in operation['parameters']}


def test_http_exchanges_cover_every_operation():
    from conftest import validator
    exchanges = read('examples/http-exchanges.json')
    expected = {(p.name, method, route) for p in APIS
                for route, methods in read(p.name)['paths'].items()
                if not route.startswith('/health') for method in methods}
    assert {(e['api'], e['method'], e['path']) for e in exchanges} == expected
    for exchange in exchanges:
        op = read(exchange['api'])['paths'][exchange['path']][exchange['method']]
        pairs = [(exchange['response'], op['responses'][exchange['status']]['content'])]
        if 'requestBody' in op:
            pairs.append((exchange['request'], op['requestBody']['content']))
        for value, content in pairs:
            filename, _, fragment = content['application/json']['schema']['$ref'].partition('#/$defs/')
            validator(filename, fragment or None).validate(value)
