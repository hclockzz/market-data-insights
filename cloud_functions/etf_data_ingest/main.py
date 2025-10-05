"""
GCP Cloud Function to ingest ETF data from Alpha Vantage API and store in GCS
"""
import json
import os
from datetime import datetime
from typing import Dict, Any
import logging

import requests
from google.cloud import storage
import functions_framework

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlphaVantageETFIngest:
    """Alpha Vantage ETF 数据获取和存储类"""
    
    def __init__(self):
        self.api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
        self.bucket_name = os.environ.get('GCS_BUCKET_NAME')
        
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY environment variable is required")
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is required")
            
        # 初始化 GCS 客户端
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.bucket_name)
    
    def get_etf_profile(self, symbol: str) -> Dict[str, Any]:
        """
        从 Alpha Vantage API 获取 ETF profile 数据
        
        Args:
            symbol: ETF 符号，例如 'QQQ'
            
        Returns:
            ETF profile 数据字典
        """
        params = {
            'function': 'ETF_PROFILE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        logger.info(f"正在获取 ETF {symbol} 的 profile 数据")
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查 API 错误
            if 'Error Message' in data:
                raise ValueError(f"Alpha Vantage API 错误: {data['Error Message']}")
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API 注意事项: {data['Note']}")
                
            return data
            
        except requests.RequestException as e:
            logger.error(f"请求 Alpha Vantage API 失败: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"解析 API 响应失败: {str(e)}")
            raise
    
    def get_etf_holdings(self, symbol: str) -> Dict[str, Any]:
        """
        从 Alpha Vantage API 获取 ETF holdings 数据
        
        Args:
            symbol: ETF 符号，例如 'QQQ'
            
        Returns:
            ETF holdings 数据字典
        """
        params = {
            'function': 'ETF_HOLDINGS',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        logger.info(f"正在获取 ETF {symbol} 的 holdings 数据")
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查 API 错误
            if 'Error Message' in data:
                raise ValueError(f"Alpha Vantage API 错误: {data['Error Message']}")
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API 注意事项: {data['Note']}")
                
            return data
            
        except requests.RequestException as e:
            logger.error(f"请求 Alpha Vantage API 失败: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"解析 API 响应失败: {str(e)}")
            raise
    
    def store_to_gcs(self, data: Dict[str, Any], symbol: str, data_type: str) -> str:
        """
        将数据存储到 Google Cloud Storage
        
        Args:
            data: 要存储的数据
            symbol: ETF 符号
            data_type: 数据类型 ('profile' 或 'holdings')
            
        Returns:
            存储的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_path = datetime.now().strftime("%Y/%m/%d")
        
        # 构造 GCS 对象路径
        blob_name = f"etf_data/{data_type}/{symbol}/{date_path}/{symbol}_{data_type}_{timestamp}.json"
        
        logger.info(f"正在将数据存储到 GCS: {blob_name}")
        
        try:
            # 创建 blob 并上传数据
            blob = self.bucket.blob(blob_name)
            
            # 添加元数据
            blob.metadata = {
                'symbol': symbol,
                'data_type': data_type,
                'ingestion_timestamp': timestamp,
                'source': 'alphavantage'
            }
            
            # 上传 JSON 数据
            blob.upload_from_string(
                data=json.dumps(data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            
            logger.info(f"数据成功存储到 GCS: gs://{self.bucket_name}/{blob_name}")
            return f"gs://{self.bucket_name}/{blob_name}"
            
        except Exception as e:
            logger.error(f"存储到 GCS 失败: {str(e)}")
            raise
    
    def ingest_etf_data(self, symbol: str, include_holdings: bool = True) -> Dict[str, str]:
        """
        完整的 ETF 数据获取和存储流程
        
        Args:
            symbol: ETF 符号
            include_holdings: 是否包含 holdings 数据
            
        Returns:
            存储结果信息
        """
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'files_created': []
        }
        
        try:
            # 获取并存储 ETF profile
            logger.info(f"开始处理 ETF {symbol} 的数据")
            
            profile_data = self.get_etf_profile(symbol)
            profile_path = self.store_to_gcs(profile_data, symbol, 'profile')
            result['files_created'].append(profile_path)
            
            # 获取并存储 ETF holdings（如果需要）
            if include_holdings:
                holdings_data = self.get_etf_holdings(symbol)
                holdings_path = self.store_to_gcs(holdings_data, symbol, 'holdings')
                result['files_created'].append(holdings_path)
            
            result['status'] = 'success'
            logger.info(f"ETF {symbol} 数据处理完成")
            
        except Exception as e:
            result['status'] = 'error'
            result['error_message'] = str(e)
            logger.error(f"处理 ETF {symbol} 数据时出错: {str(e)}")
            
        return result


@functions_framework.http
def etf_data_ingest(request):
    """
    Cloud Function HTTP 入口点
    
    Expected request format:
    {
        "symbol": "QQQ",
        "include_holdings": true
    }
    """
    try:
        # 解析请求
        if request.method != 'POST':
            return {'error': '只支持 POST 请求'}, 405
        
        request_json = request.get_json(silent=True)
        if not request_json:
            return {'error': '请求体必须是有效的 JSON'}, 400
        
        symbol = request_json.get('symbol')
        if not symbol:
            return {'error': '参数 symbol 是必需的'}, 400
        
        include_holdings = request_json.get('include_holdings', True)
        
        # 创建数据获取器实例
        ingest = AlphaVantageETFIngest()
        
        # 执行数据获取和存储
        result = ingest.ingest_etf_data(symbol, include_holdings)
        
        return result, 200 if result['status'] == 'success' else 500
        
    except Exception as e:
        logger.error(f"Cloud Function 执行失败: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500


@functions_framework.cloud_event
def etf_data_ingest_scheduled(cloud_event):
    """
    Cloud Function 定时触发入口点（可以配合 Cloud Scheduler 使用）
    
    Expected cloud event data:
    {
        "symbols": ["QQQ", "SPY", "VTI"],
        "include_holdings": true
    }
    """
    try:
        data = cloud_event.data
        symbols = data.get('symbols', [])
        include_holdings = data.get('include_holdings', True)
        
        if not symbols:
            logger.error("未提供 ETF 符号列表")
            return
        
        ingest = AlphaVantageETFIngest()
        results = []
        
        for symbol in symbols:
            logger.info(f"处理定时任务中的 ETF: {symbol}")
            result = ingest.ingest_etf_data(symbol, include_holdings)
            results.append(result)
        
        logger.info(f"定时任务完成，处理了 {len(symbols)} 个 ETF")
        return results
        
    except Exception as e:
        logger.error(f"定时 Cloud Function 执行失败: {str(e)}")
        raise
