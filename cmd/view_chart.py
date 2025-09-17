#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
# 添加父目录到Python路径，以便导入父目录中的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置matplotlib支持中文显示（在导入chart_viewer之前）
try:
    from chinese_font_config import setup_chinese_font
    setup_chinese_font()
except ImportError:
    # 如果无法导入中文字体配置模块，使用简单的配置
    try:
        import matplotlib.pyplot as plt
        import platform

        system = platform.system()
        if system == "Darwin":  # macOS
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC', 'STHeiti', 'Helvetica', 'sans-serif']
        elif system == "Windows":
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial', 'sans-serif']
        else:  # Linux
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'DejaVu Sans', 'Noto Sans CJK SC', 'sans-serif']

        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        print("✓ 已配置基本中文字体支持")
    except ImportError:
        print("⚠ matplotlib未安装，请先安装: pip install matplotlib")

from chart_viewer import TradingChartViewer
from datetime import datetime, timedelta

def main():
    """交互式图表查看器"""
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='交互式K线图查看器')
    parser.add_argument('--symbol', default='BTC/USDT', help='交易对符号 (默认: BTC/USDT)')
    parser.add_argument('--timeframe', default='5m', help='时间框架 (默认: 5m)')
    parser.add_argument('--days', type=int, default=7, help='查看最近几天的数据 (默认: 7)')
    parser.add_argument('--static', action='store_true', help='使用静态模式（不支持交互）')
    parser.add_argument('--save', help='保存图片到指定路径（自动使用静态模式）')

    args = parser.parse_args()

    viewer = TradingChartViewer()

    # 计算日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')

    print(f"查看 {args.symbol} 从 {start_date} 到 {end_date} 的{args.timeframe}K线图")

    if args.save:
        print("保存模式：使用静态图表")
        viewer.plot_kline_with_trades(
            symbol=args.symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=args.timeframe,
            save_path=args.save,
            interactive=False
        )
    elif args.static:
        print("静态模式：不支持交互功能")
        viewer.plot_kline_with_trades(
            symbol=args.symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=args.timeframe,
            interactive=False
        )
    else:
        print("交互模式：支持放大缩小和日期选择")
        print("使用工具栏进行放大缩小，点击底部按钮切换日期范围")
        viewer.plot_kline_with_trades(
            symbol=args.symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=args.timeframe,
            interactive=True
        )

if __name__ == '__main__':
    main()