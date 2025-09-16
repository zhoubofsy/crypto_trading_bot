# -*- coding: utf-8 -*-

import ccxt
import numpy as np
from typing import Dict, Any
from trading_framework import TradingPlugin, TradingSignal, SignalType, MarketData

class MeanReversionPlugin(TradingPlugin):
    """均值回归策略插件"""
    
    def __init__(self, exchange, symbol: str = 'BTC/USDT'):
        super().__init__("MeanReversion")
        self.exchange = exchange
        self.symbol = symbol
        
        # 策略参数
        self.timeframe = '1m'
        self.bb_period = 20
        self.bb_stddev = 2
        self.buy_amount_usdc = 100.0
        self.sell_percentage = 1.0
        self.max_position_usdc = 500.0
    
    def fetch_bollinger_bands(self):
        """获取布林带数据"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=self.bb_period + 1)
            if len(ohlcv) < self.bb_period + 1:
                return None, None, None, None

            closes = np.array([candle[4] for candle in ohlcv])
            last_price = closes[-1]
            sma = np.mean(closes[:-1])
            std = np.std(closes[:-1])
            
            upper_band = sma + self.bb_stddev * std
            lower_band = sma - self.bb_stddev * std

            return last_price, sma, upper_band, lower_band
        except Exception as e:
            self.logger.error(f"获取布林带数据失败: {e}")
            return None, None, None, None
    
    def analyze(self, market_data: MarketData, position_info: Dict) -> TradingSignal:
        """分析市场数据并返回交易信号"""
        last_price, sma, upper_band, lower_band = self.fetch_bollinger_bands()
        
        if not all([last_price, sma, upper_band, lower_band]):
            return TradingSignal(SignalType.HOLD, self.symbol, market_data.price, 0.0, 
                               reason="数据不足")
        
        position_size = position_info.get('position_size', 0.0)
        is_in_position = position_size > 0
        
        # 生成交易信号
        if last_price > upper_band and is_in_position:
            # 超买且有持仓 -> 卖出信号
            confidence = min(1.0, (last_price - upper_band) / (sma * 0.02))  # 基于偏离程度计算置信度
            return TradingSignal(
                SignalType.SELL, 
                self.symbol, 
                last_price, 
                confidence,
                sell_percentage=self.sell_percentage,
                reason=f"价格{last_price:.2f}高于上轨{upper_band:.2f}"
            )
        
        elif last_price < lower_band and not is_in_position:
            # 超卖且无持仓 -> 买入信号
            confidence = min(1.0, (lower_band - last_price) / (sma * 0.02))
            return TradingSignal(
                SignalType.BUY, 
                self.symbol, 
                last_price, 
                confidence,
                amount_usdc=self.buy_amount_usdc,
                reason=f"价格{last_price:.2f}低于下轨{lower_band:.2f}"
            )
        
        else:
            return TradingSignal(SignalType.HOLD, self.symbol, last_price, 0.0, 
                               reason="价格在布林带内")
    
    def get_config(self) -> Dict[str, Any]:
        """获取插件配置"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'bb_period': self.bb_period,
            'bb_stddev': self.bb_stddev,
            'buy_amount_usdc': self.buy_amount_usdc,
            'sell_percentage': self.sell_percentage,
            'max_position_usdc': self.max_position_usdc
        }