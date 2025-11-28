# agent/nl2sql.py
import re
from typing import Tuple
from agent.tools.sqlite_tool import SQLiteTool

DB_SPECIAL_NAMES = {
    "order details": '"Order Details"',
    "order_details": '"Order Details"',
    "order details": '"Order Details"',
}

def _tbl(name: str) -> str:
    """Helper to map common names to actual SQLite table names (quoted)."""
    n = name.strip().lower()
    return DB_SPECIAL_NAMES.get(n, name)

def generate_sql(question: str, db: SQLiteTool) -> Tuple[str, float]:
    """
    Produce a SQL string and a confidence score (0..1) for common query types.
    This is rule-based to work offline and demonstrates the NL->SQL step.
    """
    q = question.lower().strip()

    #  Top N products by revenue
    m = re.search(r"top\s+(\d+)\s+products\s+by\s+revenue", q)
    if m:
        n = int(m.group(1))
        sql = f'''
        SELECT p.ProductName AS product,
               SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) AS revenue
        FROM "Order Details" od
        JOIN Products p ON od.ProductID = p.ProductID
        GROUP BY p.ProductName
        ORDER BY revenue DESC
        LIMIT {n};
        '''
        return (sql.strip(), 0.95)

    #  Total revenue (optionally with date range words)
    if "total revenue" in q or "sum revenue" in q:
        # handle simple last X days pattern
        m = re.search(r"last\s+(\d+)\s+days", q)
        if m:
            days = int(m.group(1))
            sql = f'''
            SELECT SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) AS total_revenue
            FROM "Order Details" od
            JOIN Orders o ON od.OrderID = o.OrderID
            WHERE o.OrderDate >= date('now', '-{days} days');
            '''
            return (sql.strip(), 0.9)
        else:
            sql = '''
            SELECT SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) AS total_revenue
            FROM "Order Details" od;
            '''
            return (sql.strip(), 0.8)

    #  Average Order Value (AOV)
    if "average order value" in q or "aov" in q:
        sql = '''
        SELECT (SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) * 1.0) /
               (COUNT(DISTINCT od.OrderID)) AS aov
        FROM "Order Details" od;
        '''
        return (sql.strip(), 0.9)

    # Count customers / orders / products
    m = re.search(r"how many\s+(customers|orders|products)", q)
    if m:
        what = m.group(1)
        mapping = {
            "customers": "Customers",
            "orders": "Orders",
            "products": "Products",
        }
        tbl = mapping.get(what, what.capitalize())
        sql = f"SELECT COUNT(*) AS cnt FROM {tbl};"
        return (sql, 0.85)

    #  Orders in last N days
    m = re.search(r"orders\s+(in|within|last)\s+(\d+)\s+days", q)
    if m:
        days = int(m.group(2))
        sql = f'''
        SELECT COUNT(*) AS orders_last_{days}_days
        FROM Orders
        WHERE OrderDate >= date('now','-{days} days');
        '''
        return (sql.strip(), 0.88)

    # Fallback: try to build a simple select from Products when product mentioned
    if "product" in q or "products" in q:
        sql = "SELECT ProductID, ProductName, CategoryID FROM Products LIMIT 50;"
        return (sql, 0.6)

    
    return ("", 0.0)
