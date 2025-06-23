import requests

API_URL = "http://your_server_url:port"  # 此处替换成你的服务器IP地址和端口(如果不是80端口)

class JQQMTAPI:
    def __init__(self):
        self.api_url = API_URL
    
    def update_positions(self, strategy_name: str, positions: list):
        """
        更新策略持仓到数据库
        
        Args:
            strategy_name: 策略名称
            positions: 持仓列表，格式如：
                [
                    {
                        'code': '000001.XSHE',
                        'volume': 100,
                        'cost': 10.5
                    }
                ]
        """
        url = f'{self.api_url}/api/v1/positions/update'
        data = {
            'strategy_name': strategy_name,
            'positions': positions
        }
        
        response = requests.post(url, json=data)
        if response.status_code != 200:
            raise Exception(f'更新持仓失败: {response.text}')