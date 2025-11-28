# agent/tools/test_graph_pipeline.py
from agent.graph_hybrid import graph, AgentState

questions = [
    "Show top 3 products by revenue",
    "Calculate Average Order Value",
    "How many customers do we have?"
]

for q in questions:
    state = AgentState(question=q)
    result_state = graph.invoke(state)  # This returns a dict

    print(f"Question: {q}")
    print("Mode:", result_state.get("mode"))
    print("SQL:", result_state.get("sql"))
    print("Confidence:", result_state.get("nl2sql_confidence"))
    print("Result:", result_state.get("result"))
    print("Final Answer:", result_state.get("final_answer"))
    print("Execution Error:", result_state.get("execution_error"))
    print("-"*50)
