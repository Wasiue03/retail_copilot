from typing import Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from agent.router import router
from agent.rag.retrieval import Retriever
from agent.tools.sqlite_tool import SQLiteTool


class AgentState(BaseModel):
    question: str
    mode: Optional[str] = None
    chunks: Optional[list] = None
    sql: Optional[str] = None
    result: Optional[dict] = None
    nl2sql_confidence: Optional[float] = None
    execution_error: Optional[str] = None



retriever = Retriever()
db = SQLiteTool()



def node_router(state: AgentState):
    mode = router(state.question)
    return {"mode": mode}

def node_rag(state: AgentState):
    if state.mode == "rag":
        chunks = retriever.search(state.question)
        return {"chunks": chunks}
    return {}


from agent.nl2sql import generate_sql

def node_nl2sql(state: AgentState):
    
    if state.mode in ("sql", "hybrid"):
        sql, conf = generate_sql(state.question, db)
       
        return {"sql": sql, "result": None, "nl2sql_confidence": conf}
    return {}

def node_sql_executor(state: AgentState):
    """
    Execute the SQL produced by NL→SQL.
    Only runs if mode is 'sql' or 'hybrid' AND sql is non-empty.
    """
    if state.mode in ("sql", "hybrid") and state.sql:
        result = db.execute(state.sql)

        if result["error"]:
            return {
                "result": None,
                "execution_error": result["error"]
            }
        else:
            return {
                "result": result,
                "execution_error": None
            }
    return {}



graph_builder = StateGraph(AgentState)

graph_builder.add_node("router", node_router)
graph_builder.add_node("rag", node_rag)
graph_builder.add_node("sql", node_nl2sql)

graph_builder.set_entry_point("router")

graph_builder.add_edge("router", "rag")
graph_builder.add_edge("router", "sql")

graph_builder.add_edge("rag", END)
graph_builder.add_edge("sql", END)

graph_builder.add_node("sql_executor", node_sql_executor)
graph_builder.add_edge("nl2sql", "sql_executor")   
graph = graph_builder.compile()
