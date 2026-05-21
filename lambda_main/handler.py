import json
import boto3
import uuid
import datetime

# Conexión a DynamoDB en Floci
dynamodb = boto3.client(
    'dynamodb',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

TABLE_NAME = 'Tasks'

def handler(event, context):
    method = event.get('httpMethod')
    path   = event.get('path', '')

    if method == 'POST' and path == '/tasks':
        return create_task(event)
    elif method == 'GET' and path == '/tasks':
        return list_tasks(event)
    elif method == 'PUT' and path.startswith('/tasks/'):
        return complete_task(event)
    elif method == 'DELETE' and path.startswith('/tasks/'):
        return delete_task(event)
    else:
        return response(404, {'error': 'Ruta no encontrada'})

def create_task(event):
    body   = json.loads(event.get('body', '{}'))
    title  = body.get('title')
    userId = body.get('userId', 'user-1')

    if not title:
        return response(400, {'error': 'El titulo es requerido'})

    task = {
        'userId':    {'S': userId},
        'taskId':    {'S': str(uuid.uuid4())},
        'title':     {'S': title},
        'completed': {'BOOL': False},
        'createdAt': {'S': datetime.datetime.utcnow().isoformat()}
    }

    dynamodb.put_item(TableName=TABLE_NAME, Item=task)
    return response(201, {'message': 'Tarea creada', 'taskId': task['taskId']['S']})

def list_tasks(event):
    params = event.get('queryStringParameters') or {}
    userId = params.get('userId', 'user-1')

    result = dynamodb.query(
        TableName=TABLE_NAME,
        KeyConditionExpression='userId = :uid',
        ExpressionAttributeValues={':uid': {'S': userId}}
    )

    tasks = []
    for item in result.get('Items', []):
        tasks.append({
            'taskId':    item['taskId']['S'],
            'title':     item['title']['S'],
            'completed': item['completed']['BOOL'],
            'createdAt': item['createdAt']['S']
        })

    return response(200, {'tasks': tasks})

def complete_task(event):
    path   = event.get('path', '')
    taskId = path.split('/')[-1]
    body   = json.loads(event.get('body', '{}'))
    userId = body.get('userId', 'user-1')

    dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={
            'userId': {'S': userId},
            'taskId': {'S': taskId}
        },
        UpdateExpression='SET completed = :val',
        ExpressionAttributeValues={':val': {'BOOL': True}}
    )

    return response(200, {'message': 'Tarea completada'})

def delete_task(event):
    path   = event.get('path', '')
    taskId = path.split('/')[-1]
    body   = json.loads(event.get('body', '{}'))
    userId = body.get('userId', 'user-1')

    dynamodb.delete_item(
        TableName=TABLE_NAME,
        Key={
            'userId': {'S': userId},
            'taskId': {'S': taskId}
        }
    )

    return response(200, {'message': 'Tarea eliminada'})

def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body)
    }