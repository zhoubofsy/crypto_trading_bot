# -*- coding: utf-8 -*-

"""
中文字体配置模块
用于配置matplotlib支持中文显示
"""

import platform

def setup_chinese_font():
    """
    设置matplotlib支持中文显示
    
    这个函数会根据操作系统自动选择合适的中文字体，
    并配置matplotlib的字体参数以正确显示中文。
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        
        system = platform.system()
        
        # 根据操作系统定义候选字体列表
        if system == "Darwin":  # macOS
            chinese_fonts = [
                'Arial Unicode MS',  # macOS默认支持中文的字体
                'PingFang SC',       # macOS系统字体
                'Heiti SC',          # 黑体
                'STHeiti',           # 华文黑体
                'Helvetica'          # 备用字体
            ]
        elif system == "Windows":
            chinese_fonts = [
                'SimHei',            # 黑体
                'Microsoft YaHei',   # 微软雅黑
                'SimSun',            # 宋体
                'KaiTi',             # 楷体
                'Arial'              # 备用字体
            ]
        else:  # Linux
            chinese_fonts = [
                'WenQuanYi Micro Hei',  # 文泉驿微米黑
                'Noto Sans CJK SC',     # Google Noto字体
                'DejaVu Sans',          # DejaVu字体
                'Liberation Sans'       # Liberation字体
            ]
        
        # 获取系统可用字体列表
        try:
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            # 查找第一个可用的中文字体
            selected_font = None
            for font in chinese_fonts:
                if font in available_fonts:
                    selected_font = font
                    break
            
            if selected_font:
                plt.rcParams['font.sans-serif'] = [selected_font] + plt.rcParams['font.sans-serif']
                print(f"✓ 已配置中文字体: {selected_font}")
            else:
                # 如果没有找到理想的字体，使用系统默认配置
                plt.rcParams['font.sans-serif'] = chinese_fonts + ['sans-serif']
                print("⚠ 未找到理想的中文字体，使用默认配置")
                
        except Exception as e:
            # 如果字体检测失败，使用基本配置
            print(f"字体检测失败: {e}")
            plt.rcParams['font.sans-serif'] = chinese_fonts + ['sans-serif']
        
        # 解决负号显示问题
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置默认字体大小
        plt.rcParams['font.size'] = 10
        
        return True
        
    except ImportError as e:
        print(f"无法导入matplotlib: {e}")
        print("请先安装matplotlib: pip install matplotlib")
        return False
    except Exception as e:
        print(f"配置中文字体时出错: {e}")
        return False

def test_chinese_display():
    """
    测试中文显示效果
    创建一个简单的图表来验证中文是否能正确显示
    """
    if not setup_chinese_font():
        return False
    
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        # 创建测试数据
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x, y, 'b-', linewidth=2, label='正弦波')
        
        # 设置中文标题和标签
        ax.set_title('中文字体测试 - 正弦函数图', fontsize=16, fontweight='bold')
        ax.set_xlabel('时间 (秒)', fontsize=12)
        ax.set_ylabel('幅度', fontsize=12)
        
        # 添加图例和网格
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图片
        plt.savefig('chinese_font_test.png', dpi=150, bbox_inches='tight')
        print("✓ 中文字体测试图表已保存为: chinese_font_test.png")
        
        # 显示当前字体配置
        print(f"当前字体配置: {plt.rcParams['font.sans-serif'][:3]}")
        
        return True
        
    except Exception as e:
        print(f"测试中文显示时出错: {e}")
        return False

if __name__ == '__main__':
    print("正在测试中文字体配置...")
    test_chinese_display()
