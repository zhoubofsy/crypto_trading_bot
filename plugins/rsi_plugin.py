# -*- coding: utf-8 -*-

import ccxt
import numpy as np
from typing import Dict, Any
from trading_framework import TradingPlugin, TradingSignal, SignalType, MarketData

class RSIPlugin(TradingPlugin):
    """RSI策略插件"""
    
    def __init__(self, exchange, symbol: str = 'BTC/USDT'):
        super().__init__("RSI")
        self.exchange = exchange
        self.symbol = symbol
        
        # RSI参数
        self.timeframe = '1m'
        self.rsi_period = 14
        self.oversold_level = 30
        self.overbought_level = 70
        self.buy_amount_usdc = 50.0
        self.sell_percentage = 0.5  # 只卖出一半
    
    def calculate_rsi(self):
        """计算RSI指标"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=self.rsi_period + 10)
            if len(ohlcv) < self.rsi_period + 1:
                return None
            
            closes = np.array([candle[4] for candle in ohlcv])
            deltas = np.diff(closes)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-self.rsi_period:])
            avg_loss = np.mean(losses[-self.rsi_period:])
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except Exception as e:
            self.logger.error(f"计算RSI失败: {e}")
            return None
    
    def analyze(self, market_data: MarketData, position_info: Dict) -> TradingSignal:
        """分析RSI并返回交易信号"""
        rsi = self.calculate_rsi()
        
        if rsi is None:
            return TradingSignal(SignalType.HOLD, self.symbol, market_data.price, 0.0, 
                               reason="RSI计算失败")
        
        position_size = position_info.get('position_size', 0.0)
        is_in_position = position_size > 0
        
        if rsi < self.oversold_level and not is_in_position:
            # RSI超卖且无持仓 -> 买入信号
            confidence = (self.oversold_level - rsi) / self.oversold_level
            return TradingSignal(
                SignalType.BUY,
                self.symbol,
                market_data.price,
                confidence,
                amount_usdc=self.buy_amount_usdc,
                reason=f"RSI超卖({rsi:.1f})"
            )
        
        elif rsi > self.overbought_level and is_in_position:
            # RSI超买且有持仓 -> 卖出信号
            confidence = (rsi - self.overbought_level) / (100 - self.overbought_level)
            return TradingSignal(
                SignalType.SELL,
                self.symbol,
                market_data.price,
                confidence,
                sell_percentage=self.sell_percentage,
                reason=f"RSI超买({rsi:.1f})"
            )
        
        else:
            return TradingSignal(SignalType.HOLD, self.symbol, market_data.price, 0.0, 
                               reason=f"RSI正常({rsi:.1f})")
    
    def get_config(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'rsi_period': self.rsi_period,
            'oversold_level': self.oversold_level,
            'overbought_level': self.overbought_level,
            'buy_amount_usdc': self.buy_amount_usdc,
            'sell_percentage': self.sell_percentage
        }