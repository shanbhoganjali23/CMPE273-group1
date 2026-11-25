import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / 'contracts'


def read(name):
    return json.loads((CONTRACTS / name).read_text())


REGISTRY = Registry().with_resources(
    ((p.as_uri(), Resource.from_contents(json.loads(p.read_text())))
     for p in CONTRACTS.glob('*.schema.json'))
)


def validator(name, definition=None):
    uri = (CONTRACTS / name).as_uri()
    if definition:
        uri += '#/$defs/' + definition
    return Draft202012Validator({'$ref': uri}, registry=REGISTRY,
                               format_checker=FormatChecker())


@pytest.fixture
def example():
    return lambda name: read('examples/' + name + '.json')
