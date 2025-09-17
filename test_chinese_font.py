#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试中文字体显示的简单脚本
"""

import matplotlib.pyplot as plt
import platform

def setup_chinese_font():
    """设置中文字体"""
    try:
        import matplotlib.font_manager as fm
        
        system = platform.system()
        if system == "Darwin":  # macOS
            chinese_fonts = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC', 'STHeiti']
        elif system == "Windows":
            chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun']
        else:  # Linux
            chinese_fonts = ['WenQuanYi Micro Hei', 'DejaVu Sans', 'Noto Sans CJK SC']
        
        # 尝试找到可用的中文字体
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        for font in chinese_fonts:
            if font in available_fonts:
                plt.rcParams['font.sans-serif'] = [font] + plt.rcParams['font.sans-serif']
                print(f"使用中文字体: {font}")
                break
        else:
            # 如果没有找到中文字体，使用默认字体并警告
            print("警告: 未找到合适的中文字体，中文可能显示为方块")
            # 尝试使用系统默认的中文字体设置
            if system == "Darwin":  # macOS
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Helvetica', 'sans-serif']
            elif system == "Windows":
                plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'sans-serif']
            else:  # Linux
                plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'sans-serif']
        
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
    except ImportError:
        print("matplotlib.font_manager 不可用，使用基本字体配置")
        # 基本的字体配置，不依赖font_manager
        system = platform.system()
        if system == "Darwin":  # macOS
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Helvetica', 'sans-serif']
        elif system == "Windows":
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'sans-serif']
        else:  # Linux
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False

def test_chinese_display():
    """测试中文显示"""
    setup_chinese_font()
    
    # 创建一个简单的测试图表
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 测试数据
    x = [1, 2, 3, 4, 5]
    y = [2, 5, 3, 8, 7]
    
    ax.plot(x, y, 'b-o', linewidth=2, markersize=8)
    
    # 设置中文标题和标签
    ax.set_title('BTC/USDT 5分钟K线图 (测试中文显示)', fontsize=16, fontweight='bold')
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('价格 (USDT)', fontsize=12)
    
    # 添加网格
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图片而不是显示，避免在无GUI环境下出错
    plt.savefig('chinese_font_test.png', dpi=150, bbox_inches='tight')
    print("测试图表已保存为 chinese_font_test.png")
    
    # 显示当前字体设置
    print(f"当前字体设置: {plt.rcParams['font.sans-serif']}")

if __name__ == '__main__':
    test_chinese_display()
