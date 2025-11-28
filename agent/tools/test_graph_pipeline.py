from agent.graph_hybrid import graph, AgentState

q = "Show top 3 products by revenue"

# Invoke the graph
result_state = graph.invoke(AgentState(question=q))

# Access results via dict keys
print("Mode:", result_state.get("mode"))
print("SQL:", result_state.get("sql"))
print("Confidence:", result_state.get("nl2sql_confidence"))
print("Result:", result_state.get("result"))
print("Execution Error:", result_state.get("execution_error"))
