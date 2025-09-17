# -*- coding: utf-8 -*-

import sqlite3
import ccxt
import os
from datetime import datetime
from typing import Optional, Tuple

class VirtualTrader:
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS virtual_balance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usdc_balance REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                usdc_amount REAL NOT NULL,
                balance_before REAL NOT NULL,
                balance_after REAL NOT NULL,
                position_before REAL NOT NULL,
                position_after REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                datetime TEXT,  -- 添加可读日期时间
                signal_reason TEXT  -- 添加交易信号原因
            )
        ''')
        
        # 新增持仓表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS virtual_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                position_size REAL NOT NULL DEFAULT 0.0,
                avg_price REAL NOT NULL DEFAULT 0.0,
                total_cost REAL NOT NULL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize balance if empty
        cursor.execute('SELECT COUNT(*) FROM virtual_balance')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO virtual_balance (usdc_balance) VALUES (1000.0)')
        
        conn.commit()
        conn.close()
    
    def get_usdc_balance(self) -> float:
        """Get current virtual USDC balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT usdc_balance FROM virtual_balance ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0.0
    
    def update_balance(self, new_balance: float):
        """Update virtual USDC balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO virtual_balance (usdc_balance) VALUES (?)', (new_balance,))
        conn.commit()
        conn.close()

    def record_trade(self, symbol: str, action: str, amount: float, price: float, 
                    usdc_amount: float, balance_before: float, balance_after: float,
                    position_before: float, position_after: float, signal_reason: str = ""):
        """Record a trading transaction"""
        from datetime import datetime
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 添加可读的日期时间格式
        readable_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO trading_records 
            (symbol, action, amount, price, usdc_amount, balance_before, balance_after, 
             position_before, position_after, datetime, signal_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, action, amount, price, usdc_amount, balance_before, balance_after,
              position_before, position_after, readable_datetime, signal_reason))
        conn.commit()
        conn.close()

    def virtual_buy(self, symbol: str, current_price: float, buy_amount_usdc: float = 50.0, 
                   max_position_usdc: float = None, signal_reason: str = "") -> Tuple[float, float]:
        """执行虚拟买入交易"""
        usdc_balance = self.get_usdc_balance()
        
        # 检查余额是否足够
        if usdc_balance < buy_amount_usdc:
            print(f"虚拟 USDC 余额不足，当前余额: {usdc_balance:.2f}, 需要: {buy_amount_usdc:.2f}")
            return usdc_balance, self.get_position(symbol)[0]

        # 获取当前持仓
        position_size, avg_price, total_cost = self.get_position(symbol)
        
        # 检查是否超过最大持仓限制
        current_position_value = position_size * current_price
        if max_position_usdc and (current_position_value + buy_amount_usdc) > max_position_usdc:
            available_buy = max_position_usdc - current_position_value
            if available_buy <= 0:
                print(f"已达到最大持仓限制 {max_position_usdc:.2f} USDC，无法继续买入")
                return usdc_balance, position_size
            buy_amount_usdc = min(buy_amount_usdc, available_buy)
            print(f"调整买入金额至 {buy_amount_usdc:.2f} USDC 以符合持仓限制")

        amount_to_buy = buy_amount_usdc / current_price
        print(f"执行虚拟买入订单：{amount_to_buy:.4f} {symbol} @ {current_price:.2f} (金额: {buy_amount_usdc:.2f} USDC)")
        
        # 计算新的持仓信息
        new_position_size = position_size + amount_to_buy
        new_total_cost = total_cost + buy_amount_usdc
        new_avg_price = new_total_cost / new_position_size if new_position_size > 0 else 0.0
        
        new_usdc_balance = usdc_balance - buy_amount_usdc
        
        # 更新数据库
        self.update_balance(new_usdc_balance)
        self.update_position(symbol, new_position_size, new_avg_price, new_total_cost)
        self.record_trade(symbol, 'BUY', amount_to_buy, current_price, buy_amount_usdc,
                         usdc_balance, new_usdc_balance, position_size, new_position_size, signal_reason)
        
        return new_usdc_balance, new_position_size

    def virtual_sell(self, symbol: str, current_price: float, sell_percentage: float = 1.0, 
                    signal_reason: str = "") -> Tuple[float, float]:
        """执行虚拟卖出交易"""
        # 获取当前持仓
        position_size, avg_price, total_cost = self.get_position(symbol)
        
        if position_size <= 0:
            print("没有虚拟持仓可以卖出。")
            return self.get_usdc_balance(), 0.0
        
        # 计算卖出数量
        amount_to_sell = position_size * sell_percentage
        if amount_to_sell <= 0:
            print("卖出数量为0，无需执行交易。")
            return self.get_usdc_balance(), position_size
        
        usdc_balance = self.get_usdc_balance()
        usdc_gained = amount_to_sell * current_price
        
        # 计算新的持仓信息
        new_position_size = position_size - amount_to_sell
        new_total_cost = total_cost * (new_position_size / position_size) if position_size > 0 else 0.0
        new_avg_price = avg_price if new_position_size > 0 else 0.0
        
        sell_type = "全仓" if sell_percentage >= 1.0 else f"{sell_percentage*100:.1f}%"
        print(f"执行虚拟{sell_type}卖出订单：{amount_to_sell:.4f} {symbol} @ {current_price:.2f} (获得: {usdc_gained:.2f} USDC)")
        
        # 显示盈亏信息
        cost_of_sold = (amount_to_sell / position_size) * total_cost if position_size > 0 else 0.0
        profit_loss = usdc_gained - cost_of_sold
        print(f"本次交易盈亏: {profit_loss:.2f} USDC")
        
        new_usdc_balance = usdc_balance + usdc_gained
        
        # 更新数据库
        self.update_balance(new_usdc_balance)
        self.update_position(symbol, new_position_size, new_avg_price, new_total_cost)
        self.record_trade(symbol, 'SELL', amount_to_sell, current_price, usdc_gained,
                         usdc_balance, new_usdc_balance, position_size, new_position_size, signal_reason)
        
        return new_usdc_balance, new_position_size

    def get_position(self, symbol: str) -> Tuple[float, float, float]:
        """获取指定交易对的持仓信息
        Returns: (position_size, avg_price, total_cost)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT position_size, avg_price, total_cost 
            FROM virtual_positions 
            WHERE symbol = ?
        ''', (symbol,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0], result[1], result[2]
        else:
            return 0.0, 0.0, 0.0
    
    def update_position(self, symbol: str, position_size: float, avg_price: float, total_cost: float):
        """更新持仓信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 使用 INSERT OR REPLACE 来更新或插入
        cursor.execute('''
            INSERT OR REPLACE INTO virtual_positions 
            (symbol, position_size, avg_price, total_cost, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (symbol, position_size, avg_price, total_cost))
        
        conn.commit()
        conn.close()
    
    def get_all_positions(self) -> dict:
        """获取所有持仓信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT symbol, position_size, avg_price, total_cost 
            FROM virtual_positions 
            WHERE position_size > 0
        ''')
        results = cursor.fetchall()
        conn.close()
        
        positions = {}
        for row in results:
            positions[row[0]] = {
                'position_size': row[1],
                'avg_price': row[2],
                'total_cost': row[3]
            }
        return positions

class OKXTrader:
    _instance = None
    _exchange = None
    
    def __new__(cls):
        """单例模式，确保只有一个OKXTrader实例"""
        if cls._instance is None:
            cls._instance = super(OKXTrader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._exchange is None:
            self._init_exchange()
    
    def _init_exchange(self):
        """初始化交易所连接"""
        from config import Config
        
        config = Config.get_okx_config()
        self._exchange = ccxt.okx(config)
        
        # 测试连接
        try:
            self._exchange.load_markets()
            print("✓ OKX交易所连接成功")
        except Exception as e:
            print(f"✗ OKX交易所连接失败: {e}")
            raise
    
    def get_exchange(self):
        """获取交易所对象"""
        if self._exchange is None:
            self._init_exchange()
        return self._exchange
    
    def get_usdc_balance(self) -> float:
        """Get actual USDC balance from OKX"""
        try:
            balance = self._exchange.fetch_balance()
            return balance.get('USDC', {}).get('free', 0.0)
        except Exception as e:
            print(f"Error fetching OKX balance: {e}")
            return 0.0
    
    def reconnect(self):
        """重新连接交易所"""
        self._exchange = None
        self._init_exchange()

def get_balance(source: str = "virtual", **kwargs) -> float:
    """
    Get balance from different sources
    Args:
        source: 'virtual' or 'okx'
        **kwargs: 已废弃，现在使用配置文件
    """
    if source == "virtual":
        trader = VirtualTrader()
        return trader.get_usdc_balance()
    elif source == "okx":
        trader = OKXTrader()
        return trader.get_usdc_balance()
    else:
        raise ValueError("Source must be 'virtual' or 'okx'")

# 添加统一的买卖接口函数
def buy(source: str = "virtual", symbol: str = "", current_price: float = 0.0, 
        buy_amount_usdc: float = 50.0, max_position_usdc: float = None, 
        signal_reason: str = "", **kwargs) -> Tuple[float, float]:
    """执行买入操作"""
    if source == "virtual":
        trader = VirtualTrader()
        return trader.virtual_buy(symbol, current_price, buy_amount_usdc, max_position_usdc, signal_reason)
    elif source == "okx":
        raise NotImplementedError("OKX 真实交易功能尚未实现")
    else:
        raise ValueError("source 必须是 'virtual' 或 'okx'")

def sell(source: str = "virtual", symbol: str = "", current_price: float = 0.0, 
         sell_percentage: float = 1.0, signal_reason: str = "", **kwargs) -> Tuple[float, float]:
    """执行卖出操作"""
    if source == "virtual":
        trader = VirtualTrader()
        return trader.virtual_sell(symbol, current_price, sell_percentage, signal_reason)
    elif source == "okx":
        raise NotImplementedError("OKX 真实交易功能尚未实现")
    else:
        raise ValueError("source 必须是 'virtual' 或 'okx'")

def get_position(source: str = "virtual", symbol: str = "", **kwargs) -> Tuple[float, float, float]:
    """获取持仓信息"""
    if source == "virtual":
        trader = VirtualTrader()
        return trader.get_position(symbol)
    elif source == "okx":
        raise NotImplementedError("OKX 真实交易功能尚未实现")
    else:
        raise ValueError("source 必须是 'virtual' 或 'okx'")
