# -*- coding: utf-8 -*-

import os
from typing import Dict, Any

class Config:
    """配置管理类"""
    
    # OKX API配置
    OKX_CONFIG = {
        'apiKey': '6b2b3a85-c493-43d6-a972-178373d322bf',
        'secret': 'E2F09392E364BB1EEFA6B10FDDCE8305',
        'password': 'Max520917&',
        'options': {'defaultType': 'swap'},
        'sandbox': False,  # 是否使用沙盒环境
        'enableRateLimit': True,  # 启用速率限制
        'timeout': 30000,  # 超时时间(毫秒)
    }
    
    # 交易配置
    TRADING_CONFIG = {
        'default_symbol': 'BTC/USDT',
        'check_interval': 65,  # 检查间隔（秒）
        'default_buy_amount': 50.0,  # 默认买入金额
        'max_position_usdc': 500.0,  # 最大持仓限制
    }
    
    # 数据库配置
    DATABASE_CONFIG = {
        'db_path': 'trading.db',
    }
    
    @classmethod
    def get_okx_config(cls) -> Dict[str, Any]:
        """获取OKX配置"""
        return cls.OKX_CONFIG.copy()
    
    @classmethod
    def get_trading_config(cls) -> Dict[str, Any]:
        """获取交易配置"""
        return cls.TRADING_CONFIG.copy()
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """获取数据库配置"""
        return cls.DATABASE_CONFIG.copy()
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        if os.getenv('OKX_API_KEY'):
            cls.OKX_CONFIG['apiKey'] = os.getenv('OKX_API_KEY')
        if os.getenv('OKX_SECRET'):
            cls.OKX_CONFIG['secret'] = os.getenv('OKX_SECRET')
        if os.getenv('OKX_PASSWORD'):
            cls.OKX_CONFIG['password'] = os.getenv('OKX_PASSWORD')
        if os.getenv('OKX_SANDBOX'):
            cls.OKX_CONFIG['sandbox'] = os.getenv('OKX_SANDBOX').lower() == 'true'