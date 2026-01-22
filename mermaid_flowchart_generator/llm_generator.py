import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError
from mermaid_utils import sanitize_mermaid

load_dotenv()

class LLMGraphGenerator:
    def __init__(self, api_key=None):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash" 

    def generate(self, topic: str) -> str:
        prompt = f"""
Generate Mermaid flowchart code for: "{topic}"

RULES:
- Start with: graph TD
- Node IDs: A, B, C...
- One arrow per line
- Shapes only:
  ([Start])
  ["Process"]
  {{Decision}}
  (("Storage"))
- NO introduction / conclusion / overview
- NO edge labels
- NO styles or colors
- Not too complex
- Must contain real domain-specific steps
- Include cycle if applicable
- Return ONLY Mermaid code
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            code = response.text.strip()
            return sanitize_mermaid(code)
        except ClientError as e:
            print(f"LLM error ({e.status_code}): {e}. Using fallback.")
            fallback = f"""
graph TD
    A([Start: {topic}]) --> B["Core Step"]
    B --> C{{Decision}}
    C --> D["Next Step"]
    D --> E(("Storage"))
    E --> B
"""
            return fallback
