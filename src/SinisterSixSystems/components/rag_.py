import fitz  # PyMuPDF
import camelot
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# ---------------- Sentence Embeddings ----------------
embed_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")  # CPU-friendly

# ---------------- Extract Text ----------------
def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)

# ---------------- Extract Tables ----------------
def extract_tables(pdf_path):
    tables = camelot.read_pdf(pdf_path, pages="all")
    return [t.df.to_string(index=False) for t in tables]

# ---------------- Build Chunks ----------------
def build_chunks(pdf_path):
    chunks = []

    # Text chunk
    text = extract_text(pdf_path)
    chunks.append({"text": text, "type": "text", "source": pdf_path})

    # Table chunks
    for i, table_text in enumerate(extract_tables(pdf_path)):
        chunks.append({"text": table_text, "type": "table", "source": f"{pdf_path}_table_{i}"})

    return chunks

# ---------------- Build FAISS Index ----------------
def build_index(chunks):
    texts = [c["text"] for c in chunks]
    embeddings = embed_model.encode(texts, convert_to_numpy=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index

# ---------------- Retrieve Top-k Chunks ----------------
def retrieve(query, chunks, index, k=3):
    q_emb = embed_model.encode([query], convert_to_numpy=True)
    _, idx = index.search(q_emb, k)
    results = [chunks[i] for i in idx[0]]
    return results

# ---------------- Example ----------------
if __name__ == "__main__":
    pdf_path = "sample.pdf"  # replace with your PDF
    chunks = build_chunks(pdf_path)
    index = build_index(chunks)

    query = "Key findings including tables"
    results = retrieve(query, chunks, index, k=3)

    print("Top-k relevant chunks:\n")
    for r in results:
        print(f"[{r['type'].upper()} from {r['source']}]:\n{r['text']}\n{'-'*80}\n")
