## Bybit: Order Track & History

Tools for automated order tracking and historical trade analysis using the Bybit API (v5). Designed for traders, quant developers, analysts, and ML/AI enthusiasts working with real-world trading data.

---

## Features

- Collects complete history of closed USDT-linear futures trades
- Displays live open positions (optionally sends to Telegram)
- Calculates extended analytics: PnL %, fees, TP/SL hits, maker/taker status, order duration, execution type, etc.
- Prepares structured datasets for AI/ML modeling and trade statistics
- Stores all data in a local SQLite database (`account_trades.db`)
- Runs on a schedule (default: once per hour)

---

## Project Structure

| File              | Description                                                        |
|-------------------|---------------------------------------------------------------------|
| `history_trades.py` | Fetch and analyze closed trade history, store into SQLite           |
| `order_list.py`     | Display or send open positions via Telegram                        |
| `.env`              | API credentials and optional Telegram settings                     |
| `account_trades.db` | SQLite database with structured trade analytics                    |

---

## Installation

1. Install dependencies:

```bash
pip install pybit requests python-dotenv
```

2. Create a `.env` file:

```env
BYBIT_API_KEY=your_bybit_api_key
BYBIT_SECRET=your_bybit_api_secret

# Optional (for Telegram alerts)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=@your_chat_id_or_user_id
```

---

## Usage

### To track historical trades:

```bash
python history_trades.py
```

* Collects new closed trades every hour.
* Stores full analytical data in `account_trades.db`.

### To display open positions:

```bash
python order_list.py
```

* Shows all open USDT-futures positions in the console.
* If Telegram settings are enabled, messages are sent there too.

---

## Database Structure: `account_trades.db`

| Field                    | Description                                   |
| ------------------------ | --------------------------------------------- |
| `id`                     | Order ID                                      |
| `symbol`                 | Trading pair (e.g., BTCUSDT)                  |
| `side`                   | Buy or Sell                                   |
| `qty`                    | Order size (contracts)                        |
| `entry`, `exit`          | Entry and exit prices                         |
| `pnl`, `pnl_pct`         | Realized PnL in USD and as a percentage       |
| `fee`                    | Total fee (entry + exit, calculated manually) |
| `leverage`               | Leverage used                                 |
| `duration_sec`           | Trade duration in seconds                     |
| `tp_hit`, `sl_hit`       | Whether Take Profit or Stop Loss was hit      |
| `mt_close`               | Manually closed flag                          |
| `is_maker`               | Whether the trade was executed as maker       |
| `order_type`             | Market, Limit, TP, SL, etc.                   |
| `time_in_force`          | GTC, IOC, FOK, etc.                           |
| `num_fills`              | Number of executions (fills)                  |
| `opened_at`, `closed_at` | Trade open and close timestamps               |

---

## Recommendations

* Use a separate API key with read-only access.
* Never commit your `.env` file to a public repository.
* Secure your Telegram bot by using private chats or channels.

---

## Ideal For

* Quantitative analysis
* Backtesting and behavior modeling
* Data collection for reinforcement learning
* Live trading dashboards and reporting

---

## 📄 License

MIT License

