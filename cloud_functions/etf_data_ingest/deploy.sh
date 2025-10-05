#!/bin/bash

# ETF 数据获取 Cloud Function 部署脚本
# 使用前请确保已经配置了 gcloud CLI 并设置了正确的项目

set -e

# 配置变量
FUNCTION_NAME="etf-data-ingest"
REGION="us-central1"  # 修改为您的首选区域
RUNTIME="python311"
MEMORY="512MB"
TIMEOUT="540s"
MAX_INSTANCES="10"

# 检查必需的环境变量
if [ -z "$ALPHA_VANTAGE_API_KEY" ]; then
    echo "错误: 请设置 ALPHA_VANTAGE_API_KEY 环境变量"
    echo "例如: export ALPHA_VANTAGE_API_KEY=your_api_key"
    exit 1
fi

if [ -z "$GCS_BUCKET_NAME" ]; then
    echo "错误: 请设置 GCS_BUCKET_NAME 环境变量"
    echo "例如: export GCS_BUCKET_NAME=your-bucket-name"
    exit 1
fi

if [ -z "$GCP_PROJECT_ID" ]; then
    echo "错误: 请设置 GCP_PROJECT_ID 环境变量"
    echo "例如: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

echo "开始部署 Cloud Function: $FUNCTION_NAME"
echo "项目: $GCP_PROJECT_ID"
echo "区域: $REGION"
echo "存储桶: $GCS_BUCKET_NAME"

# 部署 HTTP 触发的 Cloud Function
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=$RUNTIME \
    --region=$REGION \
    --source=. \
    --entry-point=etf_data_ingest \
    --trigger=http \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --max-instances=$MAX_INSTANCES \
    --set-env-vars="ALPHA_VANTAGE_API_KEY=$ALPHA_VANTAGE_API_KEY,GCS_BUCKET_NAME=$GCS_BUCKET_NAME" \
    --allow-unauthenticated \
    --project=$GCP_PROJECT_ID

echo "部署完成！"

# 获取函数 URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --project=$GCP_PROJECT_ID --format="value(serviceConfig.uri)")

echo ""
echo "Function URL: $FUNCTION_URL"
echo ""
echo "测试命令示例:"
echo "curl -X POST \"$FUNCTION_URL\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"symbol\": \"QQQ\", \"include_holdings\": true}'"

