import sqlite3
import pathlib

DB_PATH = pathlib.Path(__file__).parents[2] / "data" / "northwind.sqlite"

class SQLiteTool:
    def __init__(self, db_path=str(DB_PATH)):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def list_tables(self):
        q = "SELECT name FROM sqlite_master WHERE type='table'"
        cur = self.conn.execute(q)
        return [row[0] for row in cur.fetchall()]

    def schema(self, table):
        q = f"PRAGMA table_info('{table}')"
        cur = self.conn.execute(q)
        return [dict(r) for r in cur.fetchall()]

    def execute(self, sql):
        try:
            # Create a new connection for each execution
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.execute(sql)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
            conn.close()  # close after use
            return {
                "columns": cols,
                "rows": [tuple(r) for r in rows],
                "error": None,
            }
        except Exception as e:
            return {"columns": [], "rows": [], "error": str(e)}

