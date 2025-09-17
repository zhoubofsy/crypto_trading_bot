-- Virtual balance table
CREATE TABLE virtual_balance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usdc_balance REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading records table
CREATE TABLE trading_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL, -- 'BUY' or 'SELL'
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
);

-- Initialize virtual balance with 1000 USDC
INSERT INTO virtual_balance (usdc_balance) VALUES (1000.0);