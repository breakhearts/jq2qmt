from src.api.jq_qmt_api import JQQMTAPI, API_URL
import traceback
def test_update_positions():
    # 初始化API客户端
    api = JQQMTAPI()
    
    # 测试数据
    strategy_name = 'hand_strategy'
    positions = [
        {
            'code': '002633.XSHE',  
            'volume': 600,
            'cost': 12.752
        }
    ]
    
    try:
        # 更新持仓
        api.update_positions(strategy_name, positions)
        print("持仓更新成功！")
        
        # 你可以通过浏览器访问以下地址查看更新结果：
        print(f"查看策略持仓: {API_URL}/api/v1/positions/strategy/{strategy_name}")
        print(f"查看总持仓: {API_URL}/api/v1/positions/total")
        
    except Exception as e:
        print(f"更新失败: {traceback.print_exc()}")

if __name__ == '__main__':
    test_update_positions()