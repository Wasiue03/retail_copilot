from agent.rag.retrieval import Retriever
r = Retriever()
print(r.search("What is the return window for beverages?", 2))
