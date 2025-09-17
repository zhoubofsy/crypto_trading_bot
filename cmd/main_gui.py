#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版GUI启动器
"""

import sys
import os

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """主函数"""
    print("启动简化版K线图GUI...")
    
    try:
        from gui.simple_chart_gui import SimpleChartGUI
        
        print("✅ GUI模块导入成功")
        print("正在创建界面...")
        
        gui = SimpleChartGUI()
        gui.run()
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保所有依赖都已安装")
        
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
