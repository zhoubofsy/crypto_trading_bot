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
    parser.add_argument('--api-key', help='OKX API key (required for okx source)')
    parser.add_argument('--secret', help='OKX secret (required for okx source)')
    parser.add_argument('--password', help='OKX password (required for okx source)')
    
    args = parser.parse_args()
    
    try:
        if args.source == 'virtual':
            balance = get_balance('virtual')
            print(f"Virtual USDC Balance: {balance:.2f}")
        elif args.source == 'okx':
            if not all([args.api_key, args.secret, args.password]):
                print("Error: OKX credentials required (--api-key, --secret, --password)")
                sys.exit(1)
            
            balance = get_balance('okx', 
                                api_key=args.api_key,
                                secret=args.secret, 
                                password=args.password)
            print(f"OKX USDC Balance: {balance:.2f}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()