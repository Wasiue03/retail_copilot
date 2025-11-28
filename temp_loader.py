from agent.rag.doc_loader import load_and_chunk_all
chunks = load_and_chunk_all()
print("Loaded chunks:", len(chunks))
print(chunks[0])
