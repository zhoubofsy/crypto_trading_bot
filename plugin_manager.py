# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'plugins'))

from trading_framework import TradingFramework
from plugins.mean_reversion_plugin import MeanReversionPlugin
from plugins.rsi_plugin import RSIPlugin
from trading import OKXTrader

def main():
    """插件管理工具"""
    # 使用统一的OKXTrader获取交易所对象
    okx_trader = OKXTrader()
    exchange = okx_trader.get_exchange()
    
    framework = TradingFramework()
    
    # 注册插件
    mean_reversion = MeanReversionPlugin(exchange)
    rsi_plugin = RSIPlugin(exchange)
    rsi_plugin.set_dependencies(["MeanReversion"])
    
    framework.register_plugin(mean_reversion)
    framework.register_plugin(rsi_plugin)
    
    # 显示插件信息
    print("已注册的插件:")
    for name, info in framework.list_plugins().items():
        print(f"\n插件名: {name}")
        print(f"  状态: {'启用' if info['enabled'] else '禁用'}")
        print(f"  依赖: {info['dependencies']}")
        print(f"  配置: {info['config']}")
    
    # 测试插件执行顺序
    print(f"\n插件执行顺序: {framework.plugin_order}")

if __name__ == '__main__':
    main()
