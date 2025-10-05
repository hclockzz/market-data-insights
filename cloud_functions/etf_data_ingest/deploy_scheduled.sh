#!/bin/bash

# ETF 数据获取定时 Cloud Function 部署脚本
# 这个版本使用 Cloud Events 触发器，可以配合 Cloud Scheduler 使用

set -e

# 配置变量
FUNCTION_NAME="etf-data-ingest-scheduled"
REGION="us-central1"  # 修改为您的首选区域
RUNTIME="python311"
MEMORY="512MB"
TIMEOUT="540s"
MAX_INSTANCES="5"

# Cloud Pub/Sub 主题名称（用于定时触发）
PUBSUB_TOPIC="etf-data-ingest-trigger"

# 检查必需的环境变量
if [ -z "$ALPHA_VANTAGE_API_KEY" ]; then
    echo "错误: 请设置 ALPHA_VANTAGE_API_KEY 环境变量"
    exit 1
fi

if [ -z "$GCS_BUCKET_NAME" ]; then
    echo "错误: 请设置 GCS_BUCKET_NAME 环境变量"
    exit 1
fi

if [ -z "$GCP_PROJECT_ID" ]; then
    echo "错误: 请设置 GCP_PROJECT_ID 环境变量"
    exit 1
fi

echo "开始部署定时 Cloud Function: $FUNCTION_NAME"

# 创建 Pub/Sub 主题（如果不存在）
gcloud pubsub topics create $PUBSUB_TOPIC --project=$GCP_PROJECT_ID || true

# 部署 Cloud Events 触发的 Cloud Function
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=$RUNTIME \
    --region=$REGION \
    --source=. \
    --entry-point=etf_data_ingest_scheduled \
    --trigger=http \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --max-instances=$MAX_INSTANCES \
    --set-env-vars="ALPHA_VANTAGE_API_KEY=$ALPHA_VANTAGE_API_KEY,GCS_BUCKET_NAME=$GCS_BUCKET_NAME" \
    --project=$GCP_PROJECT_ID

echo "定时 Cloud Function 部署完成！"

echo ""
echo "要设置定时任务，请运行以下命令创建 Cloud Scheduler 作业:"
echo ""
echo "gcloud scheduler jobs create pubsub etf-daily-ingest \\"
echo "  --schedule=\"0 9 * * 1-5\" \\"
echo "  --topic=$PUBSUB_TOPIC \\"
echo "  --message-body='{\"symbols\": [\"QQQ\", \"SPY\", \"VTI\"], \"include_holdings\": true}' \\"
echo "  --time-zone=\"America/New_York\" \\"
echo "  --project=$GCP_PROJECT_ID"
echo ""
echo "这将在每个工作日上午 9 点（纽约时间）运行 ETF 数据获取"

