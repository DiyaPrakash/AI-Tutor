import fitz
import camelot
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
from PIL import Image
from transformers import (
    BlipProcessor,
    BlipForConditionalGeneration,
    AutoTokenizer,
    AutoModelForCausalLM
)
import torch
import os
import gc


class MultimodalGraniteRAG:
    def __init__(
        self,
        pdf_path,
        image_dir="images",
        k_retrieve=3,
        granite_model="ibm-granite/granite-3.0-8b-instruct"
    ):
        self.pdf_path = pdf_path
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(exist_ok=True)
        self.k_retrieve = k_retrieve

        # ---------------- Device & dtype ----------------
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if self.device == "cuda" and torch.cuda.is_bf16_supported():
            self.llm_dtype = torch.bfloat16
        elif self.device == "cuda":
            self.llm_dtype = torch.float16
        else:
            self.llm_dtype = torch.float32

        # ---------------- LLM (Granite) ----------------
        self.llm_tokenizer = AutoTokenizer.from_pretrained(granite_model)

        self.llm_model = AutoModelForCausalLM.from_pretrained(
            granite_model,
            torch_dtype=self.llm_dtype,
            device_map="auto" if self.device == "cuda" else None
        )

        # ---------------- BLIP (CPU ONLY) ----------------
        self.processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        self.caption_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base",
            torch_dtype=torch.float32
        ).to("cpu")

        # ---------------- Embeddings (CPU) ----------------
        self.embed_model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cpu"
        )

        # ---------------- Build index ----------------
        self.chunks = self.build_multimodal_chunks()
        self.build_index()

    # ---------------- Text ----------------
    def extract_text(self):
        doc = fitz.open(self.pdf_path)
        return "\n".join(page.get_text() for page in doc)

    # ---------------- Tables ----------------
    def extract_tables(self):
        tables = camelot.read_pdf(self.pdf_path, pages="all")
        return [t.df.to_string(index=False) for t in tables]

    # ---------------- Images ----------------
    def extract_images(self):
        doc = fitz.open(self.pdf_path)
        image_paths = []

        for page_num, page in enumerate(doc):
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base = doc.extract_image(xref)
                path = self.image_dir / f"page{page_num}_img{img_index}.{base['ext']}"
                with open(path, "wb") as f:
                    f.write(base["image"])
                image_paths.append(str(path))

        return image_paths

    def caption_image(self, image_path):
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(image, return_tensors="pt")
        with torch.no_grad():
            out = self.caption_model.generate(**inputs)
        return self.processor.decode(out[0], skip_special_tokens=True)

    # ---------------- Chunks ----------------
    def build_multimodal_chunks(self):
        chunks = []

        chunks.append({
            "text": self.extract_text(),
            "type": "text",
            "source": self.pdf_path
        })

        for i, table in enumerate(self.extract_tables()):
            chunks.append({
                "text": table,
                "type": "table",
                "source": f"{self.pdf_path}_table_{i}"
            })

        for img in self.extract_images():
            caption = self.caption_image(img)
            chunks.append({
                "text": caption,
                "type": "image",
                "source": img
            })

        return chunks

    # ---------------- FAISS ----------------
    def build_index(self):
        texts = [c["text"] for c in self.chunks]
        embeddings = self.embed_model.encode(texts, convert_to_numpy=True)

        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def retrieve(self, query):
        q_emb = self.embed_model.encode([query], convert_to_numpy=True)
        _, idx = self.index.search(q_emb, self.k_retrieve)
        return [self.chunks[i] for i in idx[0]]

    # ---------------- Generation ----------------
    def generate_answer(self, query):
        docs = self.retrieve(query)

        context = "\n".join(
            f"[{d['type'].upper()} from {d['source']}]\n{d['text']}"
            for d in docs
        )

        prompt = f"""Use the context below to answer the question.
If the answer is not in the context, say "I don't know".

Context:
{context}

Question:
{query}

Answer:
"""

        inputs = self.llm_tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            output = self.llm_model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                temperature=0.2
            )

        return self.llm_tokenizer.decode(output[0], skip_special_tokens=True)

    # ---------------- CLEANUP ----------------
    def cleanup(self):
        """Free GPU and CPU memory safely"""
        del self.llm_model
        del self.caption_model
        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()


