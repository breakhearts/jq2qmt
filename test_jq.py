import src.api.jq_config as config
from src.api.jq_qmt_api import JQQMTAPI
import traceback
def test_update_positions():
    # 初始化API客户端
    api = JQQMTAPI()
    
    # 测试数据
    strategy_name = 'test_strategy'
    positions = [
        {
            'code': '600219.XSHG',  # 银华日利
            'volume': 200,
            'cost': 12
        }
    ]
    
    try:
        # 更新持仓
        api.update_positions(strategy_name, positions)
        print("持仓更新成功！")
        
        # 你可以通过浏览器访问以下地址查看更新结果：
        print(f"查看策略持仓: {config.API_URL}/api/v1/positions/strategy/{strategy_name}")
        print(f"查看总持仓: {config.API_URL}/api/v1/positions/total")
        
    except Exception as e:
        print(f"更新失败: {traceback.print_exc()}")

if __name__ == '__main__':
    test_update_positions()