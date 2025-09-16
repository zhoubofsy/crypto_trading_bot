# -*- coding: utf-8 -*-

import ccxt
import time
import numpy as np
from trading import VirtualTrader, buy, sell

def fetch_bollinger_bands(exchange, symbol, timeframe, period, stddev):
    """
    Fetches historical OHLCV data and calculates Bollinger Bands.
    """
    try:
        # Fetch OHLCV (Open, High, Low, Close, Volume) data
        # Fetch one more candle than the period for the latest calculation
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=period + 1)
        if len(ohlcv) < period + 1:
            return None, None, None, None

        # Extract closing prices
        closes = np.array([candle[4] for candle in ohlcv])
        
        # Latest price is the close of the last fetched candle
        last_price = closes[-1]
        
        # Calculate Simple Moving Average (SMA) for the specified period
        # We use closes[:-1] to avoid look-ahead bias
        sma = np.mean(closes[:-1])
        
        # Calculate Standard Deviation (StdDev)
        std = np.std(closes[:-1])
        
        # Calculate Bollinger Bands
        upper_band = sma + stddev * std
        lower_band = sma - stddev * std

        return last_price, sma, upper_band, lower_band

    except Exception as e:
        print(f"Error fetching data or calculating Bollinger Bands: {e}")
        return None, None, None, None

def main():
    """
    Main function to run the mean reversion strategy.
    """
    # 1. Exchange Configuration
    # IMPORTANT: Replace with your actual API credentials.
    # For a real application, you should handle these securely.
    # Consider using environment variables.
    exchange = ccxt.okx({
        'apiKey': '6b2b3a85-c493-43d6-a972-178373d322bf',
        'secret': 'E2F09392E364BB1EEFA6B10FDDCE8305',
        'password': 'Max520917&',
        'options': {
            'defaultType': 'swap',  # 'swap' for perpetual futures, 'spot' for spot trading
        },
    })
    
    # Check if we can connect to the exchange
    try:
        exchange.load_markets()
    except ccxt.NetworkError as e:
        print("Network error. Please check your internet connection.")
        print(f"Error details: {e}")
        return
    except ccxt.ExchangeError as e:
        print("Exchange error. Please check your API credentials.")
        print(f"Error details: {e}")
        return

    # 2. Strategy Parameters
    SYMBOL = 'BTC/USDT'     # The trading pair you want to analyze
    TIMEFRAME = '1m'        # Data timeframe (e.g., '1m', '5m', '15m')
    BB_PERIOD = 20          # Bollinger Band period
    BB_STDDEV = 2           # Bollinger Band standard deviation
    
    # 交易数量控制参数
    BUY_AMOUNT_USDC = 100.0    # 每次买入的USDC金额
    SELL_STRATEGY = "all"      # 卖出策略: "all"(全仓) 或 "partial"(部分)
    SELL_PERCENTAGE = 1.0      # 卖出比例 (0.0-1.0)
    MAX_POSITION_USDC = 500.0  # 最大持仓金额限制
    
    # Time in seconds to wait before the next check
    wait_interval = 60 * int(TIMEFRAME[:-1]) + 5

    print(f"Starting Mean Reversion Bot for {SYMBOL} on OKX...")
    
    # 3. 初始化虚拟交易器
    trader = VirtualTrader()
    position_size = 0.0
    is_in_position = False
    
    print(f"初始虚拟余额: {trader.get_usdc_balance():.2f} USDC")

    # 4. 主交易循环
    while True:
        last_price, sma, upper_band, lower_band = fetch_bollinger_bands(
            exchange, SYMBOL, TIMEFRAME, BB_PERIOD, BB_STDDEV
        )

        if not all([last_price, sma, upper_band, lower_band]):
            print("Could not get a full set of data. Retrying in 60 seconds...")
            time.sleep(60)
            continue
        
        # Print current market status
        print("-" * 50)
        print(f"Current Price: {last_price:.2f}")
        print(f"Upper Band: {upper_band:.2f}, Lower Band: {lower_band:.2f}")
        print(f"当前虚拟余额: {trader.get_usdc_balance():.2f} USDC")
        print(f"当前虚拟持仓: {position_size:.4f} {SYMBOL.split('/')[0]}")
        
        # 5. 生成交易信号并执行虚拟交易
        if last_price > upper_band and is_in_position:
            print(f"价格高于上轨 ({upper_band:.2f})，表明超买。")
            print("卖出信号！")
            
            # 使用配置的卖出策略
            usdc_balance, position_size = sell("virtual", SYMBOL, last_price, position_size, 
                                             sell_percentage=SELL_PERCENTAGE)
            is_in_position = position_size > 0  # 根据剩余持仓判断状态

        elif last_price < lower_band and not is_in_position:
            print(f"价格低于下轨 ({lower_band:.2f})，表明超卖。")
            print("买入信号！")
            
            # 使用配置的买入金额和持仓限制
            usdc_balance, position_size = buy("virtual", SYMBOL, last_price, position_size,
                                            buy_amount_usdc=BUY_AMOUNT_USDC,
                                            max_position_usdc=MAX_POSITION_USDC)
            is_in_position = position_size > 0
                
        else:
            print("价格在布林带内，无交易信号。")
        
        # 显示详细持仓信息
        position_value = position_size * last_price
        print(f"持仓状态: {'有持仓' if is_in_position else '无持仓'}")
        print(f"持仓数量: {position_size:.4f} {SYMBOL.split('/')[0]}")
        print(f"持仓价值: {position_value:.2f} USDC")
        
        # 6. 等待下一个周期
        print(f"等待 {wait_interval} 秒进行下一次检查...")
        time.sleep(wait_interval)

if __name__ == '__main__':
    main()
