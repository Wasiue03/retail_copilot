from typing import Optional, List
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from agent.router import router
from agent.rag.retrieval import Retriever
from agent.tools.sqlite_tool import SQLiteTool
from agent.nl2sql import generate_sql
import json
import pathlib

# -----------------------------
# Agent State
# -----------------------------
class AgentState(BaseModel):
    question: str
    mode: Optional[str] = None         # 'rag', 'sql', 'hybrid'
    chunks: Optional[List[dict]] = None
    sql: Optional[str] = None
    result: Optional[dict] = None
    nl2sql_confidence: Optional[float] = None
    execution_error: Optional[str] = None
    final_answer: Optional[str] = None
    repair_attempts: int = 0
    trace: Optional[List[dict]] = None

# -----------------------------
# Global instances
# -----------------------------
retriever = Retriever()
db = SQLiteTool()

TRACE_PATH = pathlib.Path(__file__).parents[1] / "outputs" / "trace.jsonl"

# -----------------------------
# Node functions
# -----------------------------

def node_router(state: AgentState):
    """Decide mode based on question keywords."""
    mode = router(state.question)
    return {"mode": mode}

def node_rag(state: AgentState):
    """Retrieve relevant document chunks if mode is RAG or hybrid."""
    if state.mode in ("rag", "hybrid"):
        chunks = retriever.search(state.question)
        return {"chunks": chunks}
    return {}

def node_nl2sql(state: AgentState):
    """Generate SQL from NL question if mode is SQL or hybrid."""
    if state.mode in ("sql", "hybrid"):
        sql, conf = generate_sql(state.question, db)
        return {"sql": sql, "nl2sql_confidence": conf, "result": None}
    return {}

def node_sql_executor(state: AgentState):
    """Execute SQL if available."""
    if state.mode in ("sql", "hybrid") and state.sql:
        res = db.execute(state.sql)
        if res["error"]:
            return {"result": None, "execution_error": res["error"]}
        else:
            return {"result": res, "execution_error": None}
    return {}

def node_synthesizer(state: AgentState):
    """
    Combine results from SQL and/or RAG and produce final answer.
    This is simplified for demonstration.
    """
    answer = ""
    if state.mode == "rag" and state.chunks:
        # Use first top chunk as answer (simple)
        answer = state.chunks[0]["text"]
    elif state.mode == "sql" and state.result:
        # Format SQL result
        cols = state.result.get("columns", [])
        rows = state.result.get("rows", [])
        answer = json.dumps({"columns": cols, "rows": rows})
    elif state.mode == "hybrid":
        # Combine SQL + RAG
        sql_text = json.dumps(state.result) if state.result else ""
        rag_text = state.chunks[0]["text"] if state.chunks else ""
        answer = f"SQL Result:\n{sql_text}\nRAG Info:\n{rag_text}"
    return {"final_answer": answer}

def node_repair_loop(state: AgentState):
    """
    If SQL execution failed, retry NL→SQL up to 2 times.
    """
    if state.execution_error and state.repair_attempts < 2:
        state.repair_attempts += 1
        # Re-generate SQL
        sql, conf = generate_sql(state.question, db)
        state.sql = sql
        state.nl2sql_confidence = conf
        # Attempt execution again
        res = db.execute(sql)
        if res["error"]:
            state.result = None
            state.execution_error = res["error"]
        else:
            state.result = res
            state.execution_error = None
    return {}

def node_checkpoint(state: AgentState):
    """
    Append current state to trace file for debugging.
    """
    state_dict = state.dict()
    if state.trace is None:
        state.trace = []
    state.trace.append(state_dict)
    
    TRACE_PATH.parent.mkdir(exist_ok=True)
    with open(TRACE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(state_dict) + "\n")
    return {}


import re

def node_planner(state: AgentState):
    """
    Extract constraints from retrieved doc chunks.
    Returns a dictionary with keys like:
    - start_date
    - end_date
    - category
    - kpi
    """
    constraints = {}
    if state.chunks:
        for chunk in state.chunks:
            text = chunk["content"]

            # --- Extract date ranges from marketing_calendar ---
            m = re.search(r"Dates:\s*(\d{4}-\d{2}-\d{2})\s*to\s*(\d{4}-\d{2}-\d{2})", text)
            if m:
                constraints["start_date"] = m.group(1)
                constraints["end_date"] = m.group(2)

            # --- Extract categories ---
            cat_match = re.findall(r"\b(Beverages|Condiments|Confections|Dairy Products|Grains/Cereals|Meat/Poultry|Produce|Seafood)\b", text)
            if cat_match:
                constraints["category"] = cat_match[0]  # take first match

            # --- Extract KPI formulas ---
            if "AOV" in text:
                constraints["kpi"] = "AOV"
            if "Gross Margin" in text:
                constraints["kpi"] = "Gross Margin"

    return {"constraints": constraints}


# -----------------------------
# Build the graph
# -----------------------------
graph_builder = StateGraph(AgentState)

# Add nodes
graph_builder.add_node("router", node_router)
graph_builder.add_node("rag", node_rag)
graph_builder.add_node("nl2sql", node_nl2sql)
graph_builder.add_node("sql_executor", node_sql_executor)
graph_builder.add_node("synthesizer", node_synthesizer)
graph_builder.add_node("repair_loop", node_repair_loop)
graph_builder.add_node("checkpoint", node_checkpoint)

# Entry point
graph_builder.set_entry_point("router")

# Edges
graph_builder.add_edge("router", "rag")
graph_builder.add_edge("router", "nl2sql")

graph_builder.add_edge("nl2sql", "sql_executor")
graph_builder.add_edge("nl2sql", "repair_loop")

graph_builder.add_edge("rag", "synthesizer")
graph_builder.add_edge("sql_executor", "synthesizer")
graph_builder.add_edge("repair_loop", "synthesizer")

graph_builder.add_edge("synthesizer", "checkpoint")
graph_builder.add_edge("checkpoint", END)

graph_builder.add_node("planner", node_planner)

# Edge connections
graph_builder.add_edge("rag", "planner")
graph_builder.add_edge("planner", "nl2sql")  # NL→SQL uses constraints



# Compile final graph
graph = graph_builder.compile()
