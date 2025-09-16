# -*- coding: utf-8 -*-

import ccxt
import time
import numpy as np

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
    TIMEFRAME = '1m'      # Data timeframe (e.g., '1m', '5m', '15m')
    BB_PERIOD = 20         # Bollinger Band period
    BB_STDDEV = 2          # Bollinger Band standard deviation
    
    # Time in seconds to wait before the next check
    # We add a buffer to ensure we get a new candle
    wait_interval = 60 * int(TIMEFRAME[:-1]) + 5

    print(f"Starting Mean Reversion Bot for {SYMBOL} on OKX...")
    
    # 3. Main Trading Loop
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
        print(f"Current Price: {last_price}")
        print(f"Upper Band: {upper_band:.2f}, Lower Band: {lower_band:.2f}")

        # 4. Generate Trading Signals
        if last_price > upper_band:
            print(f"Price is above the upper band ({upper_band:.2f}), suggesting it is overbought.")
            print("SELL SIGNAL!")
            
            # This is where you would place your SELL order
            # WARNING: This code is for demonstration only.
            # Do NOT use in production without proper risk management.
            # try:
            #     order = exchange.create_market_sell_order(SYMBOL, 0.001)
            #     print(f"Sell order placed: {order['id']}")
            # except Exception as e:
            #     print(f"Error placing sell order: {e}")

        elif last_price < lower_band:
            print(f"Price is below the lower band ({lower_band:.2f}), suggesting it is oversold.")
            print("BUY SIGNAL!")
            
            # This is where you would place your BUY order
            # WARNING: This code is for demonstration only.
            # Do NOT use in production without proper risk management.
            # try:
            #     order = exchange.create_market_buy_order(SYMBOL, 0.001)
            #     print(f"Buy order placed: {order['id']}")
            # except Exception as e:
            #     print(f"Error placing buy order: {e}")
                
        else:
            print("Price is within the bands. No trade signal.")
        
        # 5. Wait for the next cycle
        print(f"Waiting for {wait_interval} seconds for the next check...")
        time.sleep(wait_interval)

if __name__ == '__main__':
    main()
