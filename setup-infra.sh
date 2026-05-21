#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Levantando infraestructura en Floci...${NC}\n"

ENDPOINT="http://localhost:4566"
REGION="us-east-1"
AWS="aws --endpoint-url $ENDPOINT --region $REGION"

# ─── 1. DynamoDB ───────────────────────────────────────────
echo -e "${YELLOW}📦 Creando tabla DynamoDB...${NC}"

$AWS dynamodb create-table \
  --table-name Tasks \
  --attribute-definitions \
    AttributeName=userId,AttributeType=S \
    AttributeName=taskId,AttributeType=S \
  --key-schema \
    AttributeName=userId,KeyType=HASH \
    AttributeName=taskId,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  2>/dev/null && echo -e "${GREEN}✅ Tabla Tasks creada${NC}" || echo -e "${YELLOW}⚠️  Tabla Tasks ya existe${NC}"

# ─── 2. SQS ────────────────────────────────────────────────
echo -e "\n${YELLOW}📨 Creando cola SQS...${NC}"

$AWS sqs create-queue \
  --queue-name pipeline-events \
  2>/dev/null && echo -e "${GREEN}✅ Cola pipeline-events creada${NC}" || echo -e "${YELLOW}⚠️  Cola ya existe${NC}"

# ─── 3. S3 ─────────────────────────────────────────────────
echo -e "\n${YELLOW}🪣 Creando bucket S3...${NC}"

$AWS s3 mb s3://deploy-logs \
  2>/dev/null && echo -e "${GREEN}✅ Bucket deploy-logs creado${NC}" || echo -e "${YELLOW}⚠️  Bucket ya existe${NC}"

# ─── 4. Lambda ─────────────────────────────────────────────
echo -e "\n${YELLOW}⚡ Creando Lambda notificadora...${NC}"

mkdir -p lambda_notifier
cat > lambda_notifier/handler.py << 'EOF'
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
EOF

cd lambda_notifier && powershell -command "Compress-Archive -Path handler.py -DestinationPath ../lambda_notifier.zip -Force" && cd ..

$AWS lambda create-function \
  --function-name pipeline-notifier \
  --runtime python3.11 \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --handler handler.handler \
  --zip-file fileb://lambda_notifier.zip \
  2>/dev/null && echo -e "${GREEN}✅ Lambda pipeline-notifier creada${NC}" || echo -e "${YELLOW}⚠️  Lambda ya existe${NC}"

# ─── Resumen ───────────────────────────────────────────────
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Infraestructura lista!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  DynamoDB : Tasks"
echo -e "  SQS      : pipeline-events"
echo -e "  S3       : deploy-logs"
echo -e "  Lambda   : pipeline-notifier"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"