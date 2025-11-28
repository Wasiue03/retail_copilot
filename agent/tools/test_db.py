# agent/tools/test_db.py
import sqlite3
conn = sqlite3.connect("data/northwind.sqlite")
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 10;")
print("tables:", [r[0] for r in cur.fetchall()])
res = conn.execute("SELECT COUNT(*) FROM Orders;").fetchone()
print("Orders count:", res[0])
conn.close()
