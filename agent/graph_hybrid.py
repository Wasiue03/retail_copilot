# agent/graph_hybrid.py
from typing import Optional, List
from pydantic import BaseModel
from langgraph.graph import StateGraph, END

from agent.router import router
from agent.rag.retrieval import Retriever
from agent.tools.sqlite_tool import SQLiteTool
from agent.nl2sql import generate_sql

class AgentState(BaseModel):
    question: str
    mode: Optional[str] = None
    chunks: Optional[List[dict]] = None
    sql: Optional[str] = None
    result: Optional[dict] = None
    nl2sql_confidence: Optional[float] = None
    execution_error: Optional[str] = None

retriever = Retriever()
db = SQLiteTool()

def node_router(state: AgentState):
    return {"mode": router(state.question)}

def node_rag(state: AgentState):
    # only run RAG when mode is rag
    if state.mode == "rag":
        chunks = retriever.search(state.question)
        return {"chunks": chunks}
    return {}

def node_nl2sql(state: AgentState):
    if state.mode in ("sql", "hybrid"):
        sql, conf = generate_sql(state.question, db)
        return {"sql": sql, "nl2sql_confidence": conf}
    return {}

def node_sql_executor(state: AgentState):
    if state.mode in ("sql", "hybrid") and state.sql:
        res = db.execute(state.sql)
        if res["error"]:
            return {"result": None, "execution_error": res["error"]}
        else:
            return {"result": res, "execution_error": None}
    return {}

graph_builder = StateGraph(AgentState)

graph_builder.add_node("router", node_router)
graph_builder.add_node("rag", node_rag)
graph_builder.add_node("nl2sql", node_nl2sql)
graph_builder.add_node("sql_executor", node_sql_executor)

graph_builder.set_entry_point("router")

graph_builder.add_edge("router", "rag")
graph_builder.add_edge("router", "nl2sql")
graph_builder.add_edge("rag", END)
graph_builder.add_edge("nl2sql", "sql_executor")
graph_builder.add_edge("sql_executor", END)

graph = graph_builder.compile()
