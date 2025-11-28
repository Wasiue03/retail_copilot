def router(question: str):
    q = question.lower()

    # Pure RAG if asking for policy, definitions, marketing info
    rag_keywords = ["policy", "return", "definition", "campaign", "calendar"]
    if any(k in q for k in rag_keywords):
        return "rag"

    # Pure SQL if asking for numeric KPIs
    sql_keywords = ["revenue", "top", "orders", "customers", "units", "aov", "average order value"]
    if any(k in q for k in sql_keywords):
        return "sql"

    # Otherwise hybrid
    return "hybrid"
