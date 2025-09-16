# -*- coding: utf-8 -*-

import abc
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class TradingSignal:
    signal_type: SignalType
    symbol: str
    price: float
    confidence: float  # 0.0-1.0 信号强度
    amount_usdc: Optional[float] = None
    sell_percentage: Optional[float] = None
    reason: str = ""
    plugin_name: str = ""

@dataclass
class MarketData:
    symbol: str
    price: float
    timestamp: float
    additional_data: Dict[str, Any] = None

class TradingPlugin(abc.ABC):
    """交易插件基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.dependencies = []
        self.logger = logging.getLogger(f"plugin.{name}")
    
    @abc.abstractmethod
    def analyze(self, market_data: MarketData, position_info: Dict) -> TradingSignal:
        """分析市场数据并返回交易信号"""
        pass
    
    @abc.abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """获取插件配置"""
        pass
    
    def set_dependencies(self, dependencies: List[str]):
        """设置依赖的插件名称列表"""
        self.dependencies = dependencies
    
    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False

class TradingFramework:
    """交易框架主类"""
    
    def __init__(self):
        self.plugins: Dict[str, TradingPlugin] = {}
        self.plugin_order: List[str] = []
        self.running = False
        self.logger = logging.getLogger("framework")
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def register_plugin(self, plugin: TradingPlugin) -> bool:
        """注册插件"""
        if plugin.name in self.plugins:
            self.logger.warning(f"插件 {plugin.name} 已存在，将被覆盖")
        
        self.plugins[plugin.name] = plugin
        self._update_plugin_order()
        self.logger.info(f"插件 {plugin.name} 注册成功")
        return True
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件"""
        if plugin_name not in self.plugins:
            self.logger.warning(f"插件 {plugin_name} 不存在")
            return False
        
        del self.plugins[plugin_name]
        self._update_plugin_order()
        self.logger.info(f"插件 {plugin_name} 注销成功")
        return True
    
    def _update_plugin_order(self):
        """根据依赖关系更新插件执行顺序"""
        # 拓扑排序算法
        visited = set()
        temp_visited = set()
        order = []
        
        def dfs(plugin_name: str):
            if plugin_name in temp_visited:
                raise ValueError(f"检测到循环依赖: {plugin_name}")
            if plugin_name in visited:
                return
            
            temp_visited.add(plugin_name)
            
            if plugin_name in self.plugins:
                for dep in self.plugins[plugin_name].dependencies:
                    if dep in self.plugins:
                        dfs(dep)
            
            temp_visited.remove(plugin_name)
            visited.add(plugin_name)
            order.append(plugin_name)
        
        for plugin_name in self.plugins:
            if plugin_name not in visited:
                dfs(plugin_name)
        
        self.plugin_order = order
        self.logger.info(f"插件执行顺序: {self.plugin_order}")
    
    def get_trading_decision(self, market_data: MarketData, position_info: Dict) -> List[TradingSignal]:
        """获取所有插件的交易决策"""
        signals = []
        
        for plugin_name in self.plugin_order:
            plugin = self.plugins[plugin_name]
            
            if not plugin.enabled:
                continue
            
            try:
                signal = plugin.analyze(market_data, position_info)
                if signal:
                    signal.plugin_name = plugin_name
                    signals.append(signal)
                    self.logger.info(f"插件 {plugin_name} 返回信号: {signal.signal_type.value}")
            except Exception as e:
                self.logger.error(f"插件 {plugin_name} 执行出错: {e}")
        
        return signals
    
    def aggregate_signals(self, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """聚合多个插件的信号"""
        if not signals:
            return None
        
        # 按信号类型分组
        buy_signals = [s for s in signals if s.signal_type == SignalType.BUY]
        sell_signals = [s for s in signals if s.signal_type == SignalType.SELL]
        
        # 简单的投票机制
        if len(buy_signals) > len(sell_signals):
            # 选择置信度最高的买入信号
            best_signal = max(buy_signals, key=lambda x: x.confidence)
            return best_signal
        elif len(sell_signals) > len(buy_signals):
            # 选择置信度最高的卖出信号
            best_signal = max(sell_signals, key=lambda x: x.confidence)
            return best_signal
        else:
            # 信号数量相等，选择置信度最高的
            if signals:
                best_signal = max(signals, key=lambda x: x.confidence)
                if best_signal.confidence > 0.6:  # 只有高置信度才执行
                    return best_signal
        
        return None
    
    def list_plugins(self) -> Dict[str, Dict]:
        """列出所有插件信息"""
        plugin_info = {}
        for name, plugin in self.plugins.items():
            plugin_info[name] = {
                'enabled': plugin.enabled,
                'dependencies': plugin.dependencies,
                'config': plugin.get_config()
            }
        return plugin_info