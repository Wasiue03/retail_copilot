import os
import pathlib

DOCS_PATH = pathlib.Path(__file__).parents[2] / "docs"

def load_documents():
    docs = []
    for filename in os.listdir(DOCS_PATH):
        if filename.endswith(".md"):
            full_path = DOCS_PATH / filename
            text = full_path.read_text()
            docs.append({"filename": filename, "text": text})
    return docs


def chunk_document(text, filename, chunk_size=250):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i+chunk_size]
        chunk_text = " ".join(chunk_words)
        id_ = f"{filename}::chunk_{i//chunk_size}"
        chunks.append({"id": id_, "filename": filename, "text": chunk_text})
    return chunks


def load_and_chunk_all():
    all_docs = load_documents()
    chunks = []
    for d in all_docs:
        chunks += chunk_document(d["text"], d["filename"])
    return chunks
