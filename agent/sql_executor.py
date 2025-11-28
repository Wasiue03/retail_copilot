# agent/sql_executor.py
from agent.tools.sqlite_tool import SQLiteTool
from agent.nl2sql import generate_sql

db = SQLiteTool()

def sql_executor_node(state: dict):
    """
    Expects state = {"question": str, "mode": "sql" or "hybrid"}
    Outputs state["sql"], state["sql_result"], state["confidence"]
    """
    question = state.get("question", "")
    if not question or state.get("mode") not in ("sql", "hybrid"):
        return state

    sql, conf = generate_sql(question, db)
    state["sql"] = sql

    if sql:
        result = db.execute(sql)
        state["sql_result"] = result
    else:
        state["sql_result"] = {"columns": [], "rows": [], "error": "No SQL generated"}

    state["confidence"] = conf
    return state
