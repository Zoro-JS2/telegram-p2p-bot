import sqlite3
from datetime import datetime, timedelta

DB_NAME = "orders.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        user_id INTEGER,
        order_type TEXT,
        currency TEXT,
        amount REAL,
        bank TEXT,
        rate REAL,
        status TEXT DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS escrows (
        order_id INTEGER PRIMARY KEY,
        buyer_id INTEGER,
        seller_id INTEGER,
        confirmed_by_buyer INTEGER DEFAULT 0,
        confirmed_by_seller INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def add_order(username, user_id, order_type, currency, amount, bank, rate):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO orders (username, user_id, order_type, currency, amount, bank, rate)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (username, user_id, order_type, currency, amount, bank, rate))
    conn.commit()
    conn.close()

def get_orders(status='open'):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE status=? ORDER BY created_at DESC", (status,))
    result = c.fetchall()
    conn.close()
    return result

def close_order(order_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE orders SET status='closed' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

def add_escrow(order_id, buyer_id, seller_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO escrows (order_id, buyer_id, seller_id)
        VALUES (?, ?, ?)""", (order_id, buyer_id, seller_id))
    conn.commit()
    conn.close()

def confirm_escrow(order_id, who):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    field = "confirmed_by_buyer" if who == "buyer" else "confirmed_by_seller"
    c.execute(f"UPDATE escrows SET {field}=1 WHERE order_id=?", (order_id,))
    conn.commit()
    c.execute("SELECT confirmed_by_buyer, confirmed_by_seller FROM escrows WHERE order_id=?", (order_id,))
    flags = c.fetchone()
    conn.close()
    return flags == (1, 1)

def remove_old_orders():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE created_at <= datetime('now', '-1 day')")
    conn.commit()
    conn.close()

init_db()
