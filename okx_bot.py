# -*- coding: utf-8 -*-

import time
import sys
import os
from typing import Dict

# 添加插件目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'plugins'))

from trading_framework import TradingFramework, MarketData, SignalType
from trading import VirtualTrader, OKXTrader, buy, sell, get_position
from plugins.mean_reversion_plugin import MeanReversionPlugin
from plugins.rsi_plugin import RSIPlugin
from config import Config

class OKXTradingBot:
    """OKX交易机器人主类"""
    
    def __init__(self):
        # 从配置文件加载配置
        Config.from_env()  # 支持从环境变量覆盖配置
        
        # 初始化交易所（使用统一的OKXTrader）
        self.okx_trader = OKXTrader()
        self.exchange = self.okx_trader.get_exchange()
        
        # 初始化框架和虚拟交易器
        self.framework = TradingFramework()
        self.trader = VirtualTrader()
        
        # 从配置文件获取交易参数
        trading_config = Config.get_trading_config()
        self.symbol = trading_config['default_symbol']
        self.check_interval = trading_config['check_interval']
        
        # 注册插件
        self._register_plugins()
    
    def _register_plugins(self):
        """注册所有插件"""
        # 注册均值回归插件
        mean_reversion = MeanReversionPlugin(self.exchange, self.symbol)
        self.framework.register_plugin(mean_reversion)
        
        # 注册RSI插件，设置依赖关系（RSI依赖均值回归）
        rsi_plugin = RSIPlugin(self.exchange, self.symbol)
        rsi_plugin.set_dependencies(["MeanReversion"])  # RSI插件依赖均值回归插件
        self.framework.register_plugin(rsi_plugin)
        
        print("✓ 插件注册完成")
        print("插件信息:")
        for name, info in self.framework.list_plugins().items():
            print(f"  - {name}: 启用={info['enabled']}, 依赖={info['dependencies']}")
    
    def get_current_market_data(self) -> MarketData:
        """获取当前市场数据"""
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            return MarketData(
                symbol=self.symbol,
                price=ticker['last'],
                timestamp=time.time()
            )
        except Exception as e:
            print(f"获取市场数据失败: {e}")
            return None
    
    def get_position_info(self) -> Dict:
        """获取持仓信息"""
        position_size, avg_price, total_cost = get_position("virtual", self.symbol)
        return {
            'position_size': position_size,
            'avg_price': avg_price,
            'total_cost': total_cost,
            'usdc_balance': self.trader.get_usdc_balance()
        }
    
    def execute_signal(self, signal):
        """执行交易信号"""
        if signal.signal_type == SignalType.BUY:
            print(f"执行买入信号: {signal.reason}")
            usdc_balance, position_size = buy(
                "virtual", 
                signal.symbol, 
                signal.price,
                buy_amount_usdc=signal.amount_usdc or 100.0,
                signal_reason=signal.reason
            )
            print(f"买入完成，新持仓: {position_size:.4f}")
            
        elif signal.signal_type == SignalType.SELL:
            print(f"执行卖出信号: {signal.reason}")
            usdc_balance, position_size = sell(
                "virtual",
                signal.symbol,
                signal.price,
                sell_percentage=signal.sell_percentage or 1.0,
                signal_reason=signal.reason
            )
            print(f"卖出完成，剩余持仓: {position_size:.4f}")
    
    def run(self):
        """运行交易机器人"""
        print(f"🚀 OKX交易机器人启动 - {self.symbol}")
        print(f"初始余额: {self.trader.get_usdc_balance():.2f} USDC")
        
        # 显示初始持仓
        position_info = self.get_position_info()
        if position_info['position_size'] > 0:
            print(f"初始持仓: {position_info['position_size']:.4f} {self.symbol.split('/')[0]}")
            print(f"平均成本: {position_info['avg_price']:.2f} USDC")
        
        while True:
            try:
                print("\n" + "="*60)
                print(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 获取市场数据
                market_data = self.get_current_market_data()
                if not market_data:
                    print("❌ 无法获取市场数据，跳过本轮")
                    time.sleep(self.check_interval)
                    continue
                
                # 获取持仓信息
                position_info = self.get_position_info()
                
                # 显示当前状态
                print(f"💰 当前价格: {market_data.price:.2f}")
                print(f"💳 USDC余额: {position_info['usdc_balance']:.2f}")
                print(f"📊 持仓: {position_info['position_size']:.4f} {self.symbol.split('/')[0]}")
                
                if position_info['position_size'] > 0:
                    position_value = position_info['position_size'] * market_data.price
                    unrealized_pnl = position_value - position_info['total_cost']
                    print(f"💎 持仓价值: {position_value:.2f} USDC")
                    print(f"📈 未实现盈亏: {unrealized_pnl:.2f} USDC")
                
                # 获取所有插件的交易信号
                signals = self.framework.get_trading_decision(market_data, position_info)
                
                if signals:
                    print(f"📡 收到 {len(signals)} 个交易信号:")
                    for signal in signals:
                        print(f"  - {signal.plugin_name}: {signal.signal_type.value} "
                              f"(置信度: {signal.confidence:.2f}) - {signal.reason}")
                    
                    # 聚合信号并执行
                    final_signal = self.framework.aggregate_signals(signals)
                    if final_signal:
                        print(f"🎯 最终决策: {final_signal.signal_type.value} "
                              f"(来自: {final_signal.plugin_name})")
                        self.execute_signal(final_signal)
                    else:
                        print("⚖️ 信号冲突或置信度不足，保持观望")
                else:
                    print("📊 所有插件建议持有")
                
                print(f"⏳ 等待 {self.check_interval} 秒...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n👋 用户中断，正在退出...")
                break
            except Exception as e:
                print(f"❌ 运行出错: {e}")
                print("⏳ 等待 60 秒后重试...")
                time.sleep(60)

def main():
    """主函数"""
    bot = OKXTradingBot()
    bot.run()

if __name__ == '__main__':
    main()
