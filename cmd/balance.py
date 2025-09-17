#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os

# Add parent directory to path to import trading module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from trading import get_balance, VirtualTrader, OKXTrader
    HAS_TRADING_MODULE = True
except ImportError as e:
    print(f"警告: 无法导入trading模块: {e}")
    HAS_TRADING_MODULE = False

def set_virtual_balance(amount: float):
    """设置虚拟账户余额"""
    try:
        trader = VirtualTrader()
        old_balance = trader.get_usdc_balance()
        trader.update_balance(amount)
        print(f"✅ 虚拟账户余额已更新")
        print(f"   原余额: {old_balance:.2f} USDC")
        print(f"   新余额: {amount:.2f} USDC")
    except Exception as e:
        print(f"❌ 设置虚拟账户余额失败: {e}")
        sys.exit(1)

def list_all_accounts():
    """列出所有账户信息"""
    print("=" * 60)
    print("📊 账户信息总览")
    print("=" * 60)

    # 虚拟账户信息
    try:
        trader = VirtualTrader()
        virtual_balance = trader.get_usdc_balance()
        positions = trader.get_all_positions()

        print("\n🏦 虚拟账户")
        print("-" * 30)
        print(f"💰 USDC 余额: {virtual_balance:.2f}")

        if positions:
            print(f"📈 持仓信息:")
            total_position_value = 0
            for symbol, pos_info in positions.items():
                position_size = pos_info['position_size']
                avg_price = pos_info['avg_price']
                total_cost = pos_info['total_cost']
                current_value = position_size * avg_price  # 这里用平均价格估算，实际应该用当前价格

                print(f"   {symbol}:")
                print(f"     持仓数量: {position_size:.6f}")
                print(f"     平均价格: {avg_price:.2f} USDT")
                print(f"     总成本: {total_cost:.2f} USDC")
                print(f"     估算价值: {current_value:.2f} USDC")
                total_position_value += current_value

            total_value = virtual_balance + total_position_value
            print(f"📊 总资产估值: {total_value:.2f} USDC")
        else:
            print("📈 持仓信息: 无持仓")
            print(f"📊 总资产估值: {virtual_balance:.2f} USDC")

    except Exception as e:
        print(f"❌ 获取虚拟账户信息失败: {e}")

    # OKX账户信息
    try:
        okx_trader = OKXTrader()
        okx_balance = okx_trader.get_usdc_balance()

        print(f"\n🏢 OKX 真实账户")
        print("-" * 30)
        print(f"💰 USDC 余额: {okx_balance:.2f}")
        print("📈 持仓信息: 暂不支持查询")

    except Exception as e:
        print(f"\n🏢 OKX 真实账户")
        print("-" * 30)
        print(f"❌ 获取OKX账户信息失败: {e}")

    print("\n" + "=" * 60)

def main():
    if not HAS_TRADING_MODULE:
        print("❌ 无法启动: trading模块导入失败")
        print("请确保已安装所需依赖: pip install ccxt")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='账户余额管理工具')

    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 查看余额命令
    balance_parser = subparsers.add_parser('get', help='查看账户余额')
    balance_parser.add_argument('--source', choices=['virtual', 'okx'], default='virtual',
                               help='余额来源: virtual 或 okx (默认: virtual)')

    # 设置虚拟余额命令
    set_parser = subparsers.add_parser('set', help='设置虚拟账户余额')
    set_parser.add_argument('amount', type=float, help='要设置的余额金额')

    # 列出所有账户命令
    list_parser = subparsers.add_parser('list', help='列出所有账户信息')

    args = parser.parse_args()

    # 如果没有指定命令，默认显示虚拟账户余额
    if not args.command:
        try:
            balance = get_balance('virtual')
            print(f"Virtual USDC Balance: {balance:.2f}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    # 处理不同的命令
    try:
        if args.command == 'get':
            if args.source == 'virtual':
                balance = get_balance('virtual')
                print(f"Virtual USDC Balance: {balance:.2f}")
            elif args.source == 'okx':
                balance = get_balance('okx')
                print(f"OKX USDC Balance: {balance:.2f}")

        elif args.command == 'set':
            if args.amount < 0:
                print("❌ 余额金额不能为负数")
                sys.exit(1)
            set_virtual_balance(args.amount)

        elif args.command == 'list':
            list_all_accounts()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
