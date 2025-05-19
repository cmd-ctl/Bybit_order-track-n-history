import requests
import schedule
import os
import time
from pybit.unified_trading import HTTP
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
# --- CONFIGURATION ---

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- BYBIT SESSION ---
session = HTTP(
    api_key=os.environ.get("BYBIT_API_KEY"),
    api_secret=os.environ.get("BYBIT_SECRET")
)

def get_open_positions():
    try:
        response = session.get_positions(category="linear", settleCoin="USDT")
        positions = response.get("result", {}).get("list", [])
        open_positions = [p for p in positions if float(p["size"]) > 0]
        return open_positions
    except Exception as e:
        return f"Error fetching positions: {e}"

def format_positions(positions):
    if isinstance(positions, str):
        return positions

    if not positions:
        return "✅ No open positions."

    messages = []
    for pos in positions:
        try:
            created_time = int(pos.get("createdTime", 0))
            created_str = datetime.fromtimestamp(created_time / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            created_str = "N/A"

        msg = (
            f"📊 * {pos['symbol']} *\n"
            f"🔹 Side: `{pos['side']}`\n"
            f"🔸 Size: `{pos['size']}`\n"
            f"🎯 Entry Price: `{pos['avgPrice']}`\n"
            f"📈 Mark Price: `{pos['markPrice']}`\n"
            f"💰 Unrealized PnL: `{pos['unrealisedPnl']}`\n"
            f"⚖️ Leverage: `{pos['leverage']}x`\n"
            f"🚨 Liquidation Price: `{pos['liqPrice']}`\n"
            f"🕒 Opened At: `{created_str}`\n"
        )
        messages.append(msg)
    return "\n\n".join(messages)

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to send message to Telegram: {e}")

def job():
    print("[INFO] Running position check...")
    positions = get_open_positions()
    formatted = format_positions(positions)
    #send_to_telegram(formatted)
    print(formatted)
    print("[INFO] Position check completed.")

# --- SCHEDULER ---
schedule.every(1).hours.do(job)

print("[INFO] Script started. Will check open positions every hour.")
job()  # Run at startup

while True:
    schedule.run_pending()
    time.sleep(1)
