# -*- coding: utf-8 -*-

import ccxt
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from typing import Optional, Tuple
import argparse

# 配置matplotlib支持中文显示
try:
    from chinese_font_config import setup_chinese_font
    setup_chinese_font()
except ImportError:
    # 如果无法导入中文字体配置模块，使用简单的配置
    import platform
    system = platform.system()
    if system == "Darwin":  # macOS
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC', 'sans-serif']
    elif system == "Windows":
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'sans-serif']
    else:  # Linux
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'DejaVu Sans', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

class TradingChartViewer:
    """交易K线图查看器"""
    
    def __init__(self, db_path: str = "trading.db"):
        from config import Config
        
        self.db_path = db_path
        
        # 使用统一的OKXTrader获取交易所对象
        from trading import OKXTrader
        okx_trader = OKXTrader()
        self.exchange = okx_trader.get_exchange()
      
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
            return pd.DataFrame()
    
    def get_trading_records(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取交易记录"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT datetime, action, price, amount, usdc_amount, signal_reason, timestamp
            FROM trading_records 
            WHERE symbol = ? 
            AND datetime >= ? 
            AND datetime <= ?
            ORDER BY timestamp
        '''
        
        df = pd.read_sql_query(query, conn, params=(
            symbol, 
            f"{start_date} 00:00:00", 
            f"{end_date} 23:59:59"
        ))
        
        conn.close()
        
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        return df
    
    def plot_kline_with_trades(self, symbol: str, start_date: str, end_date: str, 
                              timeframe: str = '5m', save_path: Optional[str] = None):
        """绘制带交易标记的K线图"""
        # 获取K线数据
        print(f"正在获取 {symbol} 从 {start_date} 到 {end_date} 的{timeframe}K线数据...")
        kline_df = self.get_kline_data(symbol, start_date, end_date, timeframe)
        
        if kline_df.empty:
            print("未获取到K线数据")
            return
        
        # 获取交易记录
        print("正在获取交易记录...")
        trades_df = self.get_trading_records(symbol, start_date, end_date)
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), height_ratios=[3, 1])
        
        # 绘制K线图
        self._plot_candlestick(ax1, kline_df)
        
        # 标注交易点
        if not trades_df.empty:
            self._plot_trade_markers(ax1, trades_df)
        
        # 绘制成交量
        self._plot_volume(ax2, kline_df)
        
        # 设置标题和标签
        ax1.set_title(f'{symbol} {timeframe} K线图 ({start_date} ~ {end_date})', fontsize=14, fontweight='bold')
        ax1.set_ylabel('价格 (USDT)', fontsize=12)
        ax2.set_ylabel('成交量', fontsize=12)
        ax2.set_xlabel('时间', fontsize=12)
        
        # 格式化x轴
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax2.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # 添加网格
        ax1.grid(True, alpha=0.3)
        ax2.grid(True, alpha=0.3)
        
        # 添加图例
        if not trades_df.empty:
            ax1.legend(loc='upper left')
        
        plt.tight_layout()
        
        # 保存或显示图表
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        else:
            plt.show()
        
        # 打印交易统计
        self._print_trade_statistics(trades_df)
    
    def _plot_candlestick(self, ax, df):
        """绘制蜡烛图"""
        # 计算涨跌
        up = df['close'] >= df['open']
        down = ~up
        
        # 绘制实体
        ax.bar(df.loc[up, 'datetime'], df.loc[up, 'close'] - df.loc[up, 'open'], 
               bottom=df.loc[up, 'open'], color='red', alpha=0.8, width=0.0008)
        ax.bar(df.loc[down, 'datetime'], df.loc[down, 'open'] - df.loc[down, 'close'], 
               bottom=df.loc[down, 'close'], color='green', alpha=0.8, width=0.0008)
        
        # 绘制影线
        ax.vlines(df.loc[up, 'datetime'], df.loc[up, 'low'], df.loc[up, 'high'], 
                 color='red', alpha=0.8, linewidth=0.5)
        ax.vlines(df.loc[down, 'datetime'], df.loc[down, 'low'], df.loc[down, 'high'], 
                 color='green', alpha=0.8, linewidth=0.5)
    
    def _plot_trade_markers(self, ax, trades_df):
        """绘制交易标记"""
        buy_trades = trades_df[trades_df['action'] == 'BUY']
        sell_trades = trades_df[trades_df['action'] == 'SELL']
        
        if not buy_trades.empty:
            ax.scatter(buy_trades['datetime'], buy_trades['price'], 
                      color='blue', marker='^', s=100, alpha=0.8, 
                      label=f'买入 ({len(buy_trades)}次)', zorder=5)
            
            # 添加买入标注
            for _, trade in buy_trades.iterrows():
                ax.annotate(f'买入\n{trade["price"]:.2f}\n{trade["signal_reason"][:10]}', 
                           xy=(trade['datetime'], trade['price']),
                           xytext=(10, 20), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.3),
                           arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                           fontsize=8)
        
        if not sell_trades.empty:
            ax.scatter(sell_trades['datetime'], sell_trades['price'], 
                      color='orange', marker='v', s=100, alpha=0.8, 
                      label=f'卖出 ({len(sell_trades)}次)', zorder=5)
            
            # 添加卖出标注
            for _, trade in sell_trades.iterrows():
                ax.annotate(f'卖出\n{trade["price"]:.2f}\n{trade["signal_reason"][:10]}', 
                           xy=(trade['datetime'], trade['price']),
                           xytext=(10, -20), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='orange', alpha=0.3),
                           arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                           fontsize=8)
    
    def _plot_volume(self, ax, df):
        """绘制成交量"""
        colors = ['red' if close >= open else 'green' 
                 for close, open in zip(df['close'], df['open'])]
        ax.bar(df['datetime'], df['volume'], color=colors, alpha=0.6, width=0.0008)
    
    def _print_trade_statistics(self, trades_df):
        """打印交易统计信息"""
        if trades_df.empty:
            print("\n📊 交易统计: 无交易记录")
            return
        
        buy_count = len(trades_df[trades_df['action'] == 'BUY'])
        sell_count = len(trades_df[trades_df['action'] == 'SELL'])
        total_buy_amount = trades_df[trades_df['action'] == 'BUY']['usdc_amount'].sum()
        total_sell_amount = trades_df[trades_df['action'] == 'SELL']['usdc_amount'].sum()
        
        print(f"\n📊 交易统计:")
        print(f"  买入次数: {buy_count}")
        print(f"  卖出次数: {sell_count}")
        print(f"  总买入金额: {total_buy_amount:.2f} USDC")
        print(f"  总卖出金额: {total_sell_amount:.2f} USDC")
        print(f"  净盈亏: {total_sell_amount - total_buy_amount:.2f} USDC")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='交易K线图查看器')
    parser.add_argument('--symbol', default='BTC/USDT', help='交易对 (默认: BTC/USDT)')
    parser.add_argument('--start', required=True, help='开始日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='结束日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--timeframe', default='5m', help='时间周期 (默认: 5m)')
    parser.add_argument('--save', help='保存图片路径 (可选)')
    parser.add_argument('--db', default='trading.db', help='数据库路径 (默认: trading.db)')
    
    args = parser.parse_args()
    
    viewer = TradingChartViewer(args.db)
    viewer.plot_kline_with_trades(
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        timeframe=args.timeframe,
        save_path=args.save
    )

if __name__ == '__main__':
    main()