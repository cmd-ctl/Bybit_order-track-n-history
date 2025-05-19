import os
import sqlite3
from datetime import datetime, timezone
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import time
import requests
import hashlib
import hmac

# --- SETTINGS ---
load_dotenv()
API_KEY = os.environ["BYBIT_API_KEY"]
API_SECRET = os.environ["BYBIT_SECRET"]
LOAD_LIMIT = 50
SLEEP_INTERVAL = 3600  # in seconds
default_taker_fee = 0.0006
default_maker_fee = 0.0001

# --- BYBIT SESSION ---
session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET
)

# --- DATABASE SETUP ---
DB_FILE = "account_trades.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            symbol TEXT,
            side TEXT,
            qty REAL,
            entry REAL,
            exit REAL,
            pnl REAL,
            pnl_pct REAL,
            fee REAL,
            leverage INTEGER,
            duration_sec INTEGER,
            tp_hit INTEGER,
            sl_hit INTEGER,
            mt_close INTEGER,
            is_maker INTEGER,
            order_type TEXT,
            time_in_force TEXT,
            num_fills INTEGER,
            opened_at TEXT,
            closed_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_trade(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # already inserted
    finally:
        conn.close()

# --- BYBIT QUERIES ---

def get_closed_positions(limit=LOAD_LIMIT):
    response = session.get_closed_pnl(
        category="linear",
        settleCoin="USDT",
        limit=limit
    )
    return response.get("result", {}).get("list", [])

def get_order_history(symbol):
    response = session.get_order_history(
        category="linear",
        symbol=symbol,
        limit=LOAD_LIMIT
    )
    return response.get("result", {}).get("list", [])

def get_executions(symbol, start_time):
    url = "https://api.bybit.com/v5/execution/list"
    recv_window = 5000
    timestamp = str(int(time.time() * 1000))

    params = {
        "category": "linear",
        "symbol": symbol,
        "startTime": start_time,
        "limit": 50
    }

    param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    signature_payload = f"{timestamp}{API_KEY}{recv_window}{param_str}".encode()
    signature = hmac.new(
        API_SECRET.encode(), signature_payload, hashlib.sha256
    ).hexdigest()

    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": str(recv_window),
        "X-BAPI-SIGN": signature
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    return data.get("result", {}).get("list", [])


# --- ANALYSIS ---

def analyze_and_store_trades(limit=LOAD_LIMIT):
    trades = get_closed_positions(limit=limit)
    print(f"[INFO] Fetched {len(trades)} closed trades.")

    for trade in trades:
        try:
            trade_id = trade["orderId"]
            symbol = trade["symbol"]
            side = trade["side"]
            qty = float(trade["qty"])
            entry = float(trade["avgEntryPrice"])
            exit_ = float(trade["avgExitPrice"])
            pnl = float(trade["closedPnl"])
            leverage = int(trade.get("leverage", 1))

            # Time
            created_ts = int(trade["createdTime"])
            updated_ts = int(trade["updatedTime"])
            opened_at = datetime.fromtimestamp(created_ts / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            closed_at = datetime.fromtimestamp(updated_ts / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            duration_sec = (updated_ts - created_ts) // 1000

            # PnL %
            position_value = entry * qty
            pnl_pct = (pnl / position_value) * 100 if position_value != 0 else 0

            # fees and fills
            executions = get_executions(symbol, start_time=created_ts)
            is_maker = int(any(e.get("isMaker") for e in executions))
            fee_rate = default_maker_fee if is_maker else default_taker_fee
            total_fee = entry * qty * fee_rate
            num_fills = len(executions)

            # Orders: TP/SL/MT, тип, TIF
            orders = get_order_history(symbol)
            tp_hit = any("TakeProfit" in o.get("orderType", "") and o.get("updatedTime") for o in orders)
            sl_hit = any("Stop" in o.get("orderType", "") and o.get("updatedTime") for o in orders)
            mt_close = int(not tp_hit and not sl_hit)

            final_order = next((o for o in orders if o["orderId"] == trade_id), {})
            order_type = final_order.get("orderType", "Unknown")
            time_in_force = final_order.get("timeInForce", "GTC")

            row = (
                trade_id,
                symbol,
                side,
                qty,
                entry,
                exit_,
                pnl,
                pnl_pct,
                total_fee,
                leverage,
                duration_sec,
                int(tp_hit),
                int(sl_hit),
                mt_close,
                is_maker,
                order_type,
                time_in_force,
                num_fills,
                opened_at,
                closed_at
            )

            insert_trade(row)
            print(f"[+] {symbol} {side} | PnL: {pnl:.2f}$ ({pnl_pct:.2f}%) | Fee: {total_fee:.2f} | Fills: {num_fills} | TP: {tp_hit} | SL: {sl_hit} | MT: {mt_close}")

        except Exception as e:
            print(f"[ERROR] Failed to process trade {trade.get('orderId', '?')}: {e}")

# --- MAIN LOOP ---

def main():
    init_db()
    while True:
        analyze_and_store_trades(limit=LOAD_LIMIT)
        print(f"[INFO] Sleeping for {SLEEP_INTERVAL // 60} minutes...\n")
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main()
