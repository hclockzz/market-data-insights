import functions_framework

@functions_framework.http
def hello_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    url = "https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey=demo"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
            
    data = resp.json()
    
    # 检查 API 错误
    if 'Error Message' in data:
        raise ValueError(f"Alpha Vantage API 错误: {data['Error Message']}")
        
    return data