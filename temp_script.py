from agent.tools.sqlite_tool import SQLiteTool
db = SQLiteTool()
print("Tables =", db.list_tables()[:5])
print("Orders schema =", db.schema("Orders")[:3])
print("Test query =", db.execute("SELECT COUNT(*) FROM Orders;"))
