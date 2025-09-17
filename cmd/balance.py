#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os

# Add parent directory to path to import trading module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading import get_balance

def main():
    parser = argparse.ArgumentParser(description='Get account balance')
    parser.add_argument('--source', choices=['virtual', 'okx'], default='virtual',
                       help='Balance source: virtual or okx (default: virtual)')
    
    args = parser.parse_args()
    
    try:
        if args.source == 'virtual':
            balance = get_balance('virtual')
            print(f"Virtual USDC Balance: {balance:.2f}")
        elif args.source == 'okx':
            # 现在不需要传递API凭证，直接使用配置文件
            balance = get_balance('okx')
            print(f"OKX USDC Balance: {balance:.2f}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
