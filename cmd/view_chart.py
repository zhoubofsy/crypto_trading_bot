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
    """简单的图表查看示例"""
    viewer = TradingChartViewer()
    
    # 默认查看最近7天的数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"查看 BTC/USDT 从 {start_date} 到 {end_date} 的5分钟K线图")
    
    viewer.plot_kline_with_trades(
        symbol='BTC/USDT',
        start_date=start_date,
        end_date=end_date,
        timeframe='5m'
    )

if __name__ == '__main__':
    main()