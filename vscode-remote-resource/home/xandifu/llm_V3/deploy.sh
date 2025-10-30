#!/bin/bash

# Script de deploy para LLM V3 no Google Cloud Run
# Auto-scaling nativo (sem min/max instances definidos)

set -e  # Para em caso de erro

echo "=========================================="
echo "Deploy LLM V3 para Google Cloud Run"
echo "=========================================="

# Configurações
PROJECT_ID="seu-project-id"  # ALTERE PARA SEU PROJECT ID
REGION="southamerica-east1"
SERVICE_NAME="llm-v3-service"
GCS_RAG_BUCKET_NAME="seu-rag-bucket"  # ALTERE PARA SEU BUCKET RAG
GEMINI_API_KEY="sua-gemini-api-key"  # ALTERE PARA SUA API KEY

echo ""
echo "Configuração:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  RAG Bucket: $GCS_RAG_BUCKET_NAME"
echo ""

read -p "As configurações estão corretas? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Deploy cancelado. Edite o script deploy.sh com suas configurações."
    exit 1
fi

echo ""
echo "Configurando projeto GCP..."
gcloud config set project $PROJECT_ID

echo ""
echo "Fazendo deploy no Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region=$REGION \
  --platform=managed \
  --memory=2Gi \
  --cpu=1 \
  --timeout=300 \
  --cpu-boost \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=${PROJECT_ID}" \
  --set-env-vars="GCS_RAG_BUCKET_NAME=${GCS_RAG_BUCKET_NAME}" \
  --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY}"

echo ""
echo "=========================================="
echo "Deploy concluído com sucesso!"
echo "=========================================="

# Obtem e exibe a URL do serviço
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo "URL do serviço: $SERVICE_URL"
echo ""
echo "Teste o health check:"
echo "  curl $SERVICE_URL/health"
echo ""
echo "Teste o AnimaGuy:"
echo "  curl -X POST $SERVICE_URL/process \\"
echo "    -F 'mode=animaguy' \\"
echo "    -F 'text=Como fazer um bom pitch?'"
echo ""
