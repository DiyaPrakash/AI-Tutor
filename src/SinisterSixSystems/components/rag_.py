import fitz  # PyMuPDF
import camelot
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class SimpleRAG:
    def __init__(self, pdf_path, embedding_model="all-MiniLM-L6-v2", device="cpu"):
        self.pdf_path = pdf_path
        self.device = device

        # Load embedding model
        self.embed_model = SentenceTransformer(embedding_model, device=device)

        # Build chunks and index
        self.chunks = self.build_chunks()
        self.index = self.build_index()

    # ---------------- Extract Text ----------------
    def extract_text(self):
        doc = fitz.open(self.pdf_path)
        return "\n".join(page.get_text() for page in doc)

    # ---------------- Extract Tables ----------------
    def extract_tables(self):
        tables = camelot.read_pdf(self.pdf_path, pages="all")
        return [t.df.to_string(index=False) for t in tables]

    # ---------------- Build Chunks ----------------
    def build_chunks(self):
        chunks = []

        # Text chunk
        text = self.extract_text()
        chunks.append({"text": text, "type": "text", "source": self.pdf_path})

        # Table chunks
        for i, table_text in enumerate(self.extract_tables()):
            chunks.append({"text": table_text, "type": "table", "source": f"{self.pdf_path}_table_{i}"})

        return chunks

    # ---------------- Build FAISS Index ----------------
    def build_index(self):
        texts = [c["text"] for c in self.chunks]
        embeddings = self.embed_model.encode(texts, convert_to_numpy=True)
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        return index

    # ---------------- Retrieve Top-k Chunks ----------------
    def retrieve(self, query, k=3):
        q_emb = self.embed_model.encode([query], convert_to_numpy=True)
        _, idx = self.index.search(q_emb, k)
        return [self.chunks[i] for i in idx[0]]

# ---------------- Example ----------------
if __name__ == "__main__":
    pdf_path = "sample.pdf"  
    rag = SimpleRAG(pdf_path)

    query = "Key findings including tables"
    results = rag.retrieve(query, k=3)

    print("Top-k relevant chunks:\n")
    for r in results:
        print(f"[{r['type'].upper()} from {r['source']}]:\n{r['text']}\n{'-'*80}\n")
