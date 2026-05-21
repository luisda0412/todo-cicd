import json
import pytest
from unittest.mock import patch, MagicMock
from handler import handler

# ── HELPERS ──────────────────────────────────────────────────────────────────

def make_event(method, path, body=None, params=None):
    return {
        'httpMethod': method,
        'path': path,
        'body': json.dumps(body) if body else '{}',
        'queryStringParameters': params
    }

# ── TESTS DE CREAR TAREA ─────────────────────────────────────────────────────

@patch('handler.dynamodb')
def test_create_task_ok(mock_db):
    mock_db.put_item.return_value = {}

    event = make_event('POST', '/tasks', {'title': 'Aprender pytest', 'userId': 'user-1'})
    result = handler(event, {})

    assert result['statusCode'] == 201
    body = json.loads(result['body'])
    assert 'taskId' in body

@patch('handler.dynamodb')
def test_create_task_sin_titulo(mock_db):
    event = make_event('POST', '/tasks', {'userId': 'user-1'})
    result = handler(event, {})

    assert result['statusCode'] == 400
    body = json.loads(result['body'])
    assert 'error' in body

# ── TESTS DE LISTAR TAREAS ───────────────────────────────────────────────────

@patch('handler.dynamodb')
def test_list_tasks_ok(mock_db):
    mock_db.query.return_value = {
        'Items': [
            {
                'taskId':    {'S': '123'},
                'title':     {'S': 'Tarea de prueba'},
                'completed': {'BOOL': False},
                'createdAt': {'S': '2026-01-01'}
            }
        ]
    }

    event = make_event('GET', '/tasks', params={'userId': 'user-1'})
    result = handler(event, {})

    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert len(body['tasks']) == 1
    assert body['tasks'][0]['title'] == 'Tarea de prueba'

# ── TESTS DE COMPLETAR TAREA ─────────────────────────────────────────────────

@patch('handler.dynamodb')
def test_complete_task_ok(mock_db):
    mock_db.update_item.return_value = {}

    event = make_event('PUT', '/tasks/123', {'userId': 'user-1'})
    result = handler(event, {})

    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['message'] == 'Tarea completada'

# ── TESTS DE BORRAR TAREA ────────────────────────────────────────────────────

@patch('handler.dynamodb')
def test_delete_task_ok(mock_db):
    mock_db.delete_item.return_value = {}

    event = make_event('DELETE', '/tasks/123', {'userId': 'user-1'})
    result = handler(event, {})

    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['message'] == 'Tarea eliminada'

# ── TEST DE RUTA NO ENCONTRADA ───────────────────────────────────────────────

def test_ruta_no_encontrada():
    event = make_event('GET', '/ruta-inexistente')
    result = handler(event, {})

    assert result['statusCode'] == 404