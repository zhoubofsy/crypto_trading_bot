#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版K线图GUI - 避免线程问题
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sys
import os
import subprocess

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class SimpleChartGUI:
    """简化版K线图GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("K线图控制器 (简化版)")
        self.root.geometry("500x580")
        # 设置窗口位置
        self.root.eval('tk::PlaceWindow . center')
        
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面控件"""
        # 主标题
        title_label = tk.Label(self.root, text="📈 K线图控制器", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 参数设置框架
        params_frame = ttk.LabelFrame(self.root, text="参数设置", padding=10)
        params_frame.pack(fill="x", padx=20, pady=10)
        
        # 交易对选择
        tk.Label(params_frame, text="交易对:").grid(row=0, column=0, sticky="w", pady=5)
        self.symbol_var = tk.StringVar(value="BTC/USDT")
        symbol_combo = ttk.Combobox(params_frame, textvariable=self.symbol_var, width=15)
        symbol_combo['values'] = ('BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT')
        symbol_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=5)
        
        # 时间框架选择
        tk.Label(params_frame, text="时间框架:").grid(row=0, column=2, sticky="w", padx=(20, 0), pady=5)
        self.timeframe_var = tk.StringVar(value="5m")
        timeframe_combo = ttk.Combobox(params_frame, textvariable=self.timeframe_var, width=10)
        timeframe_combo['values'] = ('1m', '5m', '15m', '30m', '1h', '4h', '1d')
        timeframe_combo.grid(row=0, column=3, sticky="w", padx=(10, 0), pady=5)
        
        # 日期选择框架
        date_frame = ttk.LabelFrame(self.root, text="日期范围", padding=10)
        date_frame.pack(fill="x", padx=20, pady=10)
        
        # 快速日期选择
        quick_frame = tk.Frame(date_frame)
        quick_frame.pack(fill="x", pady=5)
        
        tk.Label(quick_frame, text="快速选择:").pack(side="left")
        
        quick_buttons = [
            ("最近1天", 1),
            ("最近3天", 3),
            ("最近7天", 7),
            ("最近30天", 30)
        ]
        
        for text, days in quick_buttons:
            btn = tk.Button(quick_frame, text=text, 
                          command=lambda d=days: self.set_quick_date(d))
            btn.pack(side="left", padx=5)
        
        # 自定义日期选择
        custom_frame = tk.Frame(date_frame)
        custom_frame.pack(fill="x", pady=10)
        
        tk.Label(custom_frame, text="开始日期:").grid(row=0, column=0, sticky="w")
        self.start_date_var = tk.StringVar()
        start_entry = tk.Entry(custom_frame, textvariable=self.start_date_var, width=12)
        start_entry.grid(row=0, column=1, padx=(10, 20))
        
        tk.Label(custom_frame, text="结束日期:").grid(row=0, column=2, sticky="w")
        self.end_date_var = tk.StringVar()
        end_entry = tk.Entry(custom_frame, textvariable=self.end_date_var, width=12)
        end_entry.grid(row=0, column=3, padx=(10, 0))
        
        # 设置默认日期（最近7天）
        self.set_quick_date(7)
        
        # 操作按钮框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        # 打开图表按钮
        open_btn = tk.Button(button_frame, text="📊 打开新图表", 
                           command=self.open_chart, 
                           font=("Arial", 12, "bold"),
                           bg="#1B1C1B", fg="black", 
                           height=2)
        open_btn.pack(fill="x", pady=(0, 10))
        
        # 说明文本
        info_frame = ttk.LabelFrame(self.root, text="使用说明", padding=10)
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        info_text = """📋 使用方法:
1. 设置交易对和时间框架
2. 选择日期范围
3. 点击相应按钮打开图表

🎯 三种模式:
• 打开新图表: 在新进程中打开，避免冲突
• 原版本交互: 支持快捷键，但可能有冲突
• 静态版本: 简单稳定，无交互功能

⌨️ 快捷键 (在图表窗口中):
1/3/7: 切换日期范围  r: 重置  q: 退出"""
        
        info_label = tk.Label(info_frame, text=info_text, justify="left", 
                            font=("Arial", 9), wraplength=400)
        info_label.pack()
        
    def set_quick_date(self, days):
        """设置快速日期"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        self.start_date_var.set(start_date.strftime('%Y-%m-%d'))
        self.end_date_var.set(end_date.strftime('%Y-%m-%d'))
        
    def validate_dates(self):
        """验证日期格式"""
        try:
            start_date = self.start_date_var.get().strip()
            end_date = self.end_date_var.get().strip()
            
            if not start_date or not end_date:
                raise ValueError("日期不能为空")
            
            # 验证日期格式
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start_dt >= end_dt:
                raise ValueError("开始日期必须早于结束日期")
                
            return start_date, end_date
            
        except ValueError as e:
            messagebox.showerror("日期错误", f"日期格式错误: {e}\n请使用 YYYY-MM-DD 格式")
            return None, None
    
    # def open_chart(self):
    #     """在新进程中打开图表"""
    #     # 验证日期
    #     start_date, end_date = self.validate_dates()
    #     if not start_date or not end_date:
    #         return
        
    #     symbol = self.symbol_var.get()
    #     timeframe = self.timeframe_var.get()
        
    #     try:
    #         # 构建命令行参数
    #         cmd = [
    #             sys.executable, 
    #             'cmd/view_chart.py',
    #             '--symbol', symbol,
    #             '--timeframe', timeframe,
    #             '--start-date', start_date,
    #             '--end-date', end_date,
    #             '--static'  # 使用静态模式避免冲突
    #         ]
            
    #         # 在新进程中启动
    #         subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
            
    #         messagebox.showinfo("成功", f"图表已在新窗口中打开\n{symbol} {timeframe} ({start_date} ~ {end_date})")
            
    #     except Exception as e:
    #         messagebox.showerror("错误", f"打开图表失败: {e}")
    
    def open_chart(self):
        """使用原版本的交互模式"""
        # 验证日期
        start_date, end_date = self.validate_dates()
        if not start_date or not end_date:
            return
        
        symbol = self.symbol_var.get()
        timeframe = self.timeframe_var.get()
        
        # 计算天数
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end_dt - start_dt).days
        
        try:
            cmd = [
                sys.executable,
                'cmd/view_chart.py',
                '--symbol', symbol,
                '--timeframe', timeframe,
                '--days', str(days)
            ]

            # 从gui目录执行，需要指向项目根目录
            subprocess.Popen(cmd, cwd=project_root)
            
            messagebox.showinfo("成功", f"交互式图表已启动\n支持快捷键: 1/3/7/d/r/q")
            
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {e}")
    
    # def open_original_static(self):
    #     """使用原版本的静态模式"""
    #     # 验证日期
    #     start_date, end_date = self.validate_dates()
    #     if not start_date or not end_date:
    #         return
        
    #     symbol = self.symbol_var.get()
    #     timeframe = self.timeframe_var.get()
        
    #     # 计算天数
    #     start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    #     end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    #     days = (end_dt - start_dt).days
        
    #     try:
    #         cmd = [
    #             sys.executable, 
    #             'cmd/view_chart.py',
    #             '--symbol', symbol,
    #             '--timeframe', timeframe,
    #             '--days', str(days),
    #             '--static'
    #         ]
            
    #         subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
            
    #         messagebox.showinfo("成功", f"静态图表已启动\n使用matplotlib工具栏进行操作")
            
    #     except Exception as e:
    #         messagebox.showerror("错误", f"启动失败: {e}")
    
    def run(self):
        """运行主循环"""
        self.root.mainloop()

def main():
    """主函数"""
    try:
        gui = SimpleChartGUI()
        gui.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
