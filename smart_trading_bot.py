
import ccxt
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from trading import OKXTrader
import talib
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

class TradingData:
    def __init__(self, exchange, symbol: str = 'BTC/USDT'):
        self.exchange = exchange
        self.symbol = symbol
        # Initialize other necessary attributes here

    def get_kline_data(self, symbol: str, start_date: str, end_date: str, timeframe: str = '5m') -> pd.DataFrame:
        """获取K线数据"""
        try:
            # 转换日期格式
            start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
            end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
            
            # 获取K线数据
            ohlcv_data = []
            current_timestamp = start_timestamp
            
            while current_timestamp < end_timestamp:
                try:
                    ohlcv = self.exchange.fetch_ohlcv(
                        symbol, 
                        timeframe, 
                        since=current_timestamp,
                        limit=1000
                    )
                    
                    if not ohlcv:
                        break
                    
                    ohlcv_data.extend(ohlcv)
                    current_timestamp = ohlcv[-1][0] + 1
                    
                    # 避免请求过于频繁
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"获取K线数据出错: {e}")
                    break
            
            # 转换为DataFrame
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df[(df['timestamp'] >= start_timestamp) & (df['timestamp'] <= end_timestamp)]
            
            return df.sort_values('timestamp').reset_index(drop=True)
            
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            # 返回空DataFrame，但包含必要的列
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'datetime'])

class SmartBTCUSDTBot:
    def __init__(self, trading_data):
        self.trading_data = trading_data

    def calc_TA(self):
        btc_data = self.trading_data.get_kline_data('BTC/USDT', '2025-01-01', '2025-04-01', '1m')
        # 确保你的 DataFrame 已经包含了价格数据 (close, high, low)
        # 假设你的 df 已经通过第一步的代码获取
        close = np.array(btc_data['close'])
        high = np.array(btc_data['high'])
        low = np.array(btc_data['low'])

        # 计算 RSI
        btc_data['RSI'] = talib.RSI(close, timeperiod=14)

        # 计算 MACD
        macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        btc_data['MACD'] = macd
        btc_data['MACD_Signal'] = macdsignal

        # 计算布林带
        upper, middle, lower = talib.BBANDS(close, timeperiod=20)
        btc_data['BB_Upper'] = upper
        btc_data['BB_Middle'] = middle
        btc_data['BB_Lower'] = lower

        # 打印前几行，可以看到新增的指标列
        print(btc_data.tail())
        self.training_data = btc_data

    def training(self):
        btc_data = self.training_data
        # 创建目标标签 (Y)
        # 如果第二天的收盘价上涨超过0.5%，则为买入信号 (1)
        btc_data['future_close'] = btc_data['close'].shift(-1)
        btc_data['price_change'] = (btc_data['future_close'] - btc_data['close']) / btc_data['close']
        btc_data['signal'] = np.where(btc_data['price_change'] > 0.005, 1, 0)
        # 删除最后一行，因为它没有未来价格
        btc_data.dropna(inplace=True)

        # 定义特征 (X) 和标签 (Y)
        features = ['RSI', 'MACD', 'MACD_Signal', 'BB_Upper', 'BB_Lower']
        X = btc_data[features]
        y = btc_data['signal']

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 构建并训练随机森林分类器
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        self.model = model
        # 评估模型
        predictions = model.predict(X_test)
        print(classification_report(y_test, predictions))

    def deduct(self, price):
        predictions = self.modul.predict(price)
        return predictions

if __name__ == "__main__":
    trading_data = TradingData(OKXTrader().get_exchange())
    bot = SmartBTCUSDTBot(trading_data)
    if bot:
        bot.calc_TA()
        bot.training()
        print("训练完成")    # bot.run()  # Uncomment to run the bot loop
    print("Done.")
