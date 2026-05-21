import json
import boto3
import datetime

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def handler(event, context):
    for record in event.get('Records', []):
        body = json.loads(record['body'])
        status  = body.get('status', 'unknown')
        branch  = body.get('branch', 'unknown')
        commit  = body.get('commit', 'unknown')

        log = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "status": status,
            "branch": branch,
            "commit": commit
        }

        filename = f"deploy-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
        s3.put_object(
            Bucket='deploy-logs',
            Key=filename,
            Body=json.dumps(log, indent=2)
        )

        print(f"✅ Log guardado: {filename} — status: {status}")

    return {"statusCode": 200}
