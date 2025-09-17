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
# 交互功能的可选导入
try:
    from matplotlib.widgets import Button
    INTERACTIVE_AVAILABLE = True
except ImportError:
    INTERACTIVE_AVAILABLE = False

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
            # 返回空DataFrame，但包含必要的列
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'datetime'])
    
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
                              timeframe: str = '5m', save_path: Optional[str] = None, interactive: bool = True):
        """绘制带交易标记的K线图"""
        if interactive and save_path is None:
            # 使用交互式模式
            self._plot_interactive_kline(symbol, start_date, end_date, timeframe)
        else:
            # 使用静态模式
            self._plot_static_kline(symbol, start_date, end_date, timeframe, save_path)

    def _plot_static_kline(self, symbol: str, start_date: str, end_date: str,
                          timeframe: str = '5m', save_path: Optional[str] = None):
        """绘制静态K线图（原有功能）"""
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

        # 打印交易统计
        self._print_trade_statistics(trades_df)

    def _plot_interactive_kline(self, symbol: str, start_date: str, end_date: str, timeframe: str = '5m'):
        """绘制交互式K线图，支持放大缩小和日期选择"""
        if not INTERACTIVE_AVAILABLE:
            print("交互功能不可用，使用静态模式")
            self._plot_static_kline(symbol, start_date, end_date, timeframe)
            return

        # 存储当前参数
        self.current_symbol = symbol
        self.current_timeframe = timeframe
        self.original_start_date = start_date
        self.original_end_date = end_date

        # 获取初始数据
        self._refresh_chart_data(start_date, end_date)

        # 创建交互式图表
        self._create_interactive_chart()

    def _refresh_chart_data(self, start_date: str, end_date: str):
        """刷新图表数据"""
        print(f"正在获取 {self.current_symbol} 从 {start_date} 到 {end_date} 的{self.current_timeframe}K线数据...")
        self.kline_df = self.get_kline_data(self.current_symbol, start_date, end_date, self.current_timeframe)

        if not self.kline_df.empty:
            print("正在获取交易记录...")
            self.trades_df = self.get_trading_records(self.current_symbol, start_date, end_date)
        else:
            self.trades_df = pd.DataFrame()

    def _create_interactive_chart(self):
        """创建交互式图表"""
        if self.kline_df.empty:
            print("未获取到K线数据")
            return

        # 创建图表窗口
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(15, 10), height_ratios=[3, 1])

        # 绘制图表
        self._update_chart_display()

        # 添加键盘事件监听
        self._add_keyboard_shortcuts()

        # 显示使用说明
        self._show_usage_instructions()

        # 显示图表
        plt.show()

    def _update_chart_display(self):
        """更新图表显示"""
        # 清除之前的内容
        self.ax1.clear()
        self.ax2.clear()

        # 绘制K线图
        self._plot_candlestick(self.ax1, self.kline_df)

        # 标注交易点
        if not self.trades_df.empty:
            self._plot_trade_markers(self.ax1, self.trades_df)

        # 绘制成交量
        self._plot_volume(self.ax2, self.kline_df)

        # 设置标题和标签
        if not self.kline_df.empty and 'datetime' in self.kline_df.columns:
            start_str = self.kline_df['datetime'].iloc[0].strftime('%Y-%m-%d')
            end_str = self.kline_df['datetime'].iloc[-1].strftime('%Y-%m-%d')
        else:
            start_str = ''
            end_str = ''
        self.ax1.set_title(f'{self.current_symbol} {self.current_timeframe} K线图 ({start_str} ~ {end_str})',
                          fontsize=14, fontweight='bold')
        self.ax1.set_ylabel('价格 (USDT)', fontsize=12)
        self.ax2.set_ylabel('成交量', fontsize=12)
        self.ax2.set_xlabel('时间', fontsize=12)

        # 格式化x轴
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        self.ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        self.ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        self.ax2.xaxis.set_major_locator(mdates.HourLocator(interval=6))

        plt.setp(self.ax1.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(self.ax2.xaxis.get_majorticklabels(), rotation=45)

        # 添加网格
        self.ax1.grid(True, alpha=0.3)
        self.ax2.grid(True, alpha=0.3)

        # 添加图例
        if not self.trades_df.empty:
            self.ax1.legend(loc='upper left')

        # 刷新图表
        self.fig.canvas.draw()

    def _add_keyboard_shortcuts(self):
        """添加键盘快捷键"""
        def on_key_press(event):
            print(f"检测到按键: '{event.key}'")  # 调试信息
            if event.key == '1':
                print("切换到最近1天")
                self._change_date_range(1)
            elif event.key == '3':
                print("切换到最近3天")
                self._change_date_range(3)
            elif event.key == '7':
                print("切换到最近7天")
                self._change_date_range(7)
            elif event.key == 'd':
                print("打开日期选择对话框...")
                # 尝试多种方法来显示日期输入
                self._show_date_input_multiple_methods()
            elif event.key == 'r':
                print("重置到原始日期范围")
                # 重置到原始日期范围
                self._refresh_chart_data(self.original_start_date, self.original_end_date)
                self._update_chart_display()
                print("已重置到原始日期范围")
            elif event.key == 'q':
                print("退出程序")
                plt.close()

        # 连接键盘事件
        self.fig.canvas.mpl_connect('key_press_event', on_key_press)

    def _show_usage_instructions(self):
        """显示使用说明"""
        print("\n" + "="*50)
        print("🎯 交互式K线图使用说明")
        print("="*50)
        print("🔍 放大缩小操作:")
        print("  - 使用工具栏的放大镜工具")
        print("  - 点击并拖拽选择要放大的区域")
        print("  - 使用工具栏的后退/前进按钮撤销操作")
        print("")
        print("⌨️  键盘快捷键:")
        print("  - 按 '1': 切换到最近1天数据")
        print("  - 按 '3': 切换到最近3天数据")
        print("  - 按 '7': 切换到最近7天数据")
        print("  - 按 'd': 自定义日期范围 (会弹出输入框)")
        print("  - 按 'r': 重置到原始日期范围")
        print("")
        print("💡 重要提示:")
        print("  1. 确保图表窗口处于活动状态 (点击图表区域)")
        print("  2. 按键后会在控制台显示操作信息")
        print("  3. 如果 'd' 键没有弹出对话框，请查看控制台输出")
        print("="*50 + "\n")

    def _change_date_range(self, days: int):
        """改变日期范围"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # 刷新数据
        self._refresh_chart_data(start_date, end_date)

        # 更新显示
        self._update_chart_display()

        print(f"已切换到最近{days}天的数据")

    def _show_date_picker(self):
        """显示日期选择对话框（简化版本）"""
        self._show_console_date_input()

    def _show_console_date_input(self):
        """使用控制台输入日期"""
        print("\n=== 日期输入 ===")
        try:
            start_date = input("请输入开始日期 (YYYY-MM-DD): ").strip()
            if not start_date:
                print("取消输入")
                return

            end_date = input("请输入结束日期 (YYYY-MM-DD): ").strip()
            if not end_date:
                print("取消输入")
                return

            self._process_date_input(start_date, end_date)

        except KeyboardInterrupt:
            print("\n用户取消输入")
        except Exception as e:
            print(f"控制台输入错误: {e}")

    def _process_date_input(self, start_date, end_date):
        """处理日期输入结果"""
        try:
            # 验证日期格式
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')

            print("日期格式验证通过，正在刷新数据...")
            # 刷新数据
            self._refresh_chart_data(start_date, end_date)
            self._update_chart_display()
            print(f"✅ 已切换到 {start_date} ~ {end_date} 的数据")
        except ValueError as ve:
            print(f"❌ 日期格式错误: {ve}")
            print("请使用 YYYY-MM-DD 格式，例如: 2024-01-15")

    def _plot_candlestick(self, ax, df):
        """绘制蜡烛图"""
        if df.empty:
            ax.text(0.5, 0.5, '暂无K线数据', transform=ax.transAxes,
                   ha='center', va='center', fontsize=14, alpha=0.7)
            return

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
        if df.empty:
            ax.text(0.5, 0.5, '暂无成交量数据', transform=ax.transAxes,
                   ha='center', va='center', fontsize=12, alpha=0.7)
            return

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