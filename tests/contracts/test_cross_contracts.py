import copy

import pytest

from tests.contracts.conftest import read


def check_bundle(request, diagnosis):
    evidence = request['evidence']
    assert request['incidentId'] == evidence['incidentId'] == diagnosis['incidentId']
    assert request['targetOrderId'] == evidence['targetOrderId']
    records = evidence['records']
    assert len({r['id'] for r in records}) == len(records)
    assert request['graph']['traceId'] in request['traceIds']
    assert diagnosis['graphCompleteness'] == request['graph']['completeness']
    if diagnosis['status'] == 'AVAILABLE':
        assert set(diagnosis['evidenceIds']) <= {r['id'] for r in records if r['availability'] == 'AVAILABLE'}
        recommendation = diagnosis.get('recommendedAction')
        if recommendation:
            assert recommendation['actionId'] in request['allowedActionIds']
            assert recommendation['targetOrderId'] == request['targetOrderId']


def check_graph(graph):
    nodes = graph['nodes']
    ids = {n['id'] for n in nodes}
    assert len(ids) == len(nodes)
    assert len({e['id'] for e in graph['edges']}) == len(graph['edges'])
    for n in nodes:
        assert n['id'] == n['traceId'] + ':' + n['spanId']
    for e in graph['edges']:
        assert e['source'] in ids and e['target'] in ids
        if e['type'] == 'MESSAGE_CORRELATION':
            assert 'eventId' in e
    assert (graph['completeness'] == 'COMPLETE') == (not graph['gaps'])


def test_linked_examples(example):
    request, diagnosis = example('analysis-request'), example('diagnosis')
    check_bundle(request, diagnosis)
    action = example('recovery-action')
    order, event = example('order-response'), example('order-event')
    assert action['incidentId'] == request['incidentId']
    assert action['targetOrderId'] == request['targetOrderId'] == order['orderId'] == event['orderId']
    assert order['reservationGeneration'] == event['reservationGeneration'] == 0
    assert order['attempt'] == event['attempt'] == 1
    assert event['context']['traceparent'].split('-')[1] == order['traceId']
    catalog = read('action-catalog.json')['actions']
    assert [a['actionId'] for a in catalog] == request['allowedActionIds']
    assert catalog[0]['requiresApproval'] is True
    for name in ['graph-complete', 'graph-partial']:
        check_graph(example(name))


@pytest.mark.parametrize('mutation', ['evidence', 'target', 'action', 'incident', 'availability'])
def test_reject_inconsistent_diagnosis(mutation, example):
    request, diagnosis = example('analysis-request'), example('diagnosis')
    if mutation == 'evidence':
        diagnosis['evidenceIds'] = ['00000000-0000-4000-8000-000000000099']
    elif mutation == 'target':
        diagnosis['recommendedAction']['targetOrderId'] = diagnosis['diagnosisId']
    elif mutation == 'action':
        request['allowedActionIds'] = []
    elif mutation == 'incident':
        diagnosis['incidentId'] = diagnosis['diagnosisId']
    else:
        request['evidence']['records'][0]['availability'] = 'UNAVAILABLE'
    with pytest.raises(AssertionError):
        check_bundle(request, diagnosis)


def test_reject_dangling_graph(example):
    graph = example('graph-complete')
    graph['nodes'].pop()
    with pytest.raises(AssertionError):
        check_graph(graph)


def test_shared_types_and_routes():
    definitions = read('common.schema.json')['$defs']
    assert definitions['OrderState']['enum'] == ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REVIEW_REQUIRED']
    assert definitions['Outcome']['properties']['reservationGeneration'] == definitions['Generation']
    assert definitions['ReservationRequest']['properties']['reservationGeneration'] == definitions['Generation']
    assert definitions['Target']['properties']['actionId'] == definitions['ActionRequest']['properties']['actionId']
    assert '/internal/orders/{orderId}/retries' in read('order-api.yaml')['paths']
    assert '/actions/{recoveryActionId}/approval' in read('control-api.yaml')['paths']
