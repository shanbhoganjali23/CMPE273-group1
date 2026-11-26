import pytest
from jsonschema import Draft202012Validator, ValidationError

from tests.contracts.conftest import CONTRACTS, read, validator

CASES = {
    'order-request': ('common.schema.json', 'Item'),
    'order-response': ('common.schema.json', 'Order'),
    'order-event': ('message.schema.json', None),
    'graph-complete': ('graph.schema.json', None),
    'graph-partial': ('graph.schema.json', None),
    'incident-evidence': ('incident-evidence.schema.json', None),
    'diagnosis': ('diagnosis.schema.json', None),
    'analysis-unavailable': ('diagnosis.schema.json', None),
    'recovery-action': ('common.schema.json', 'RecoveryAction'),
    'analysis-request': ('common.schema.json', 'AnalysisRequest'),
    'error': ('error.schema.json', None),
}


@pytest.mark.parametrize('name', CASES)
def test_examples(name, example):
    validator(*CASES[name]).validate(example(name))


def test_every_example_is_covered():
    assert {p.stem for p in (CONTRACTS / 'examples').glob('*.json') if p.stem != 'http-exchanges'} == set(CASES)


@pytest.mark.parametrize('path', sorted(CONTRACTS.glob('*.schema.json')))
def test_schema_definition(path):
    Draft202012Validator.check_schema(read(path.name))


@pytest.mark.parametrize('name,source', [
    ('message-zero-trace', 'order-event'),
    ('negative-generation', 'order-event'),
    ('unknown-action', 'recovery-action'),
    ('unavailable-with-cause', 'analysis-unavailable'),
    ('zero-quantity', 'order-request'),
])
def test_invalid_fixtures(name, source):
    with pytest.raises(ValidationError):
        validator(*CASES[source]).validate(read('examples/invalid/' + name + '.json'))


@pytest.mark.parametrize('field,value', [
    ('orderId', 'not-a-uuid'), ('attempt', 4), ('occurredAt', 'yesterday'),
    ('context', {}), ('reservationGeneration', -1), ('unexpected', True),
])
def test_malformed_event(field, value, example):
    event = example('order-event')
    event[field] = value
    with pytest.raises(ValidationError):
        validator('message.schema.json').validate(event)


@pytest.mark.parametrize('definition,value', [
    ('PaymentFault', {'mode': 'latency', 'ttlSeconds': 10}),
    ('PaymentFault', {'mode': 'latency', 'ttlSeconds': 10, 'latencyMs': 5001}),
    ('WorkerFault', {'mode': 'error', 'ttlSeconds': 10}),
    ('WorkerFault', {'mode': 'pause', 'ttlSeconds': 301}),
    ('Approval', {'decision': 'APPROVE', 'expectedVersion': 0, 'approverIdentity': 'spoof'}),
])
def test_invalid_controls(definition, value):
    with pytest.raises(ValidationError):
        validator('common.schema.json', definition).validate(value)


def test_verification_required_for_success(example):
    action = example('recovery-action')
    action['status'] = 'SUCCEEDED'
    with pytest.raises(ValidationError):
        validator('common.schema.json', 'RecoveryAction').validate(action)
    action['verification'] = dict(orderCompleted=True, uniquePayment=True, stockCorrect=True)
    validator('common.schema.json', 'RecoveryAction').validate(action)
