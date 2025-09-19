
import ccxt
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from trading import OKXTrader
import talib
import numpy as np
import os
import pickle
import time

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

class TradingData:
    def __init__(self, exchange, symbol: str = 'BTC/USDT'):
        self.exchange = exchange
        self.symbol = symbol
        # 确保data目录存在
        self.data_dir = 'data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"✅ 创建数据目录: {self.data_dir}")

    def _get_daily_filename(self, symbol: str, date: str, timeframe: str) -> str:
        """生成按日期命名的文件名"""
        symbol_safe = symbol.replace('/', '_')  # BTC/USDT -> BTC_USDT
        return f"{symbol_safe}_{timeframe}_{date}.dat"

    def save_daily_ohlcv(self, symbol: str, date: str, timeframe: str, ohlcv_data: list):
        """按日期名称保存OHLCV数据到.dat文件"""
        try:
            filename = self._get_daily_filename(symbol, date, timeframe)
            filepath = os.path.join(self.data_dir, filename)

            # 使用pickle保存数据，保持数据类型
            with open(filepath, 'wb') as f:
                pickle.dump(ohlcv_data, f)

            print(f"💾 保存日数据: {filename} ({len(ohlcv_data)} 条记录)")
            return True

        except Exception as e:
            print(f"❌ 保存日数据失败 {date}: {e}")
            return False

    def load_daily_ohlcv(self, symbol: str, date: str, timeframe: str) -> list:
        """按日期名称读取OHLCV数据"""
        try:
            filename = self._get_daily_filename(symbol, date, timeframe)
            filepath = os.path.join(self.data_dir, filename)

            if not os.path.exists(filepath):
                return None

            # 使用pickle读取数据
            with open(filepath, 'rb') as f:
                ohlcv_data = pickle.load(f)

            print(f"📁 读取日数据: {filename} ({len(ohlcv_data)} 条记录)")
            return ohlcv_data

        except Exception as e:
            print(f"❌ 读取日数据失败 {date}: {e}")
            return None

    def _fetch_single_day_data(self, symbol: str, date: str, timeframe: str) -> list:
        """获取单日K线数据，支持超过1000条的多次请求"""
        try:
            # 计算当日的开始和结束时间戳
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            start_timestamp = int(date_obj.timestamp() * 1000)
            end_timestamp = int((date_obj + timedelta(days=1)).timestamp() * 1000)

            print(f"🌐 从交易所获取 {symbol} {date} 的 {timeframe} 数据...")

            ohlcv_data = []
            current_timestamp = start_timestamp
            request_count = 0

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

                    # 过滤出当日数据
                    daily_ohlcv = [candle for candle in ohlcv if start_timestamp <= candle[0] < end_timestamp]

                    if not daily_ohlcv:
                        break

                    ohlcv_data.extend(daily_ohlcv)
                    current_timestamp = daily_ohlcv[-1][0] + 1
                    request_count += 1

                    # 避免请求过于频繁
                    time.sleep(0.1)

                    # 如果已经获取到当日结束时间，跳出循环
                    if daily_ohlcv[-1][0] >= end_timestamp - 1:
                        break

                except Exception as e:
                    print(f"❌ 获取数据出错: {e}")
                    break

            print(f"✅ 完成 {date} 数据获取: {len(ohlcv_data)} 条记录 (请求 {request_count} 次)")
            return ohlcv_data

        except Exception as e:
            print(f"❌ 获取单日数据失败 {date}: {e}")
            return []

    def get_kline_data(self, symbol: str, start_date: str, end_date: str, timeframe: str = '5m') -> pd.DataFrame:
        """获取K线数据 - 按天缓存"""
        try:
            print(f"📊 获取K线数据: {symbol} {timeframe} ({start_date} ~ {end_date})")

            # 生成日期范围
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')

            all_ohlcv_data = []
            current_dt = start_dt

            while current_dt <= end_dt:
                date_str = current_dt.strftime('%Y-%m-%d')

                # 尝试从缓存读取数据
                cached_data = self.load_daily_ohlcv(symbol, date_str, timeframe)

                if cached_data is not None:
                    # 使用缓存数据
                    all_ohlcv_data.extend(cached_data)
                else:
                    # 从交易所获取数据
                    daily_data = self._fetch_single_day_data(symbol, date_str, timeframe)

                    if daily_data:
                        # 保存到缓存
                        self.save_daily_ohlcv(symbol, date_str, timeframe, daily_data)
                        all_ohlcv_data.extend(daily_data)
                    else:
                        print(f"⚠️ {date_str} 无数据")

                # 移动到下一天
                current_dt += timedelta(days=1)

            # 转换为DataFrame
            if all_ohlcv_data:
                df = pd.DataFrame(all_ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('timestamp').reset_index(drop=True)

                # 去重（可能存在重叠数据）
                df = df.drop_duplicates(subset=['timestamp']).reset_index(drop=True)

                print(f"✅ 数据获取完成: 总计 {len(df)} 条记录")
                return df
            else:
                print("❌ 未获取到任何数据")
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'datetime'])

        except Exception as e:
            print(f"❌ 获取K线数据失败: {e}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'datetime'])
    def calc_TA(self):
        btc_data = self.get_kline_data('BTC/USDT', '2025-01-01', '2025-04-01', '1m')
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
    def sign_data(self):
        btc_data = self.training_data
        # 创建目标标签 (Y)
        # 如果第二天的收盘价上涨超过0.5%，则为买入信号 (1)
        btc_data['future_close'] = btc_data['close'].shift(-1)
        btc_data['price_change'] = (btc_data['future_close'] - btc_data['close']) / btc_data['close']
        btc_data['signal'] = np.where(btc_data['price_change'] > 0.005, 1, 0)
        # 删除最后一行，因为它没有未来价格
        btc_data.dropna(inplace=True)
        self.btc_data = btc_data

class SmartBTCUSDTBot:
    def __init__(self, btc_data):
        self.btc_data = btc_data

    def training(self):
        btc_data = self.btc_data

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
    # 预读，确保数据已经下载
    start_date = '2025-01-01'
    end_date = '2025-04-01'

    trading_data = TradingData(OKXTrader().get_exchange())
    trading_data.get_kline_data('BTC/USDT', start_date, end_date, '1m')
    trading_data.calc_TA()
    trading_data.sign_data()
    bot = SmartBTCUSDTBot(trading_data.btc_data)
    if bot:
        bot.training()
        print("训练完成")    # bot.run()  # Uncomment to run the bot loop
    print("Done.")
