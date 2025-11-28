from agent.graph_hybrid import node_planner, AgentState

# Simulate retrieved RAG chunks
chunks = [
    {
        "id": "marketing_calendar::chunk0",
        "content": """
## Summer Beverages 1997
- Dates: 1997-06-01 to 1997-06-30
- Notes: Focus on Beverages and Condiments.
"""
    },
    {
        "id": "catalog::chunk1",
        "content": "Categories include Beverages, Condiments, Confections, Dairy Products."
    }
]

# Create AgentState
state = AgentState(
    question="Total revenue from the 'Beverages' category during 'Summer Beverages 1997' dates.",
    mode="hybrid",
    chunks=chunks
)

# Run planner node
output = node_planner(state)

print("Planner Output:")
print(output)
