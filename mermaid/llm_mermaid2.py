"""
LLM-based Mermaid Graph Generator
Generates intelligent, topic-specific flowcharts with proper graph IDs
using Google Gemini API (UPDATED).
"""

import os
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class LLMGraphGenerator:
    """
    Uses LLM (Google Gemini API) to generate intelligent Mermaid flowchart syntax
    with proper graph IDs and topic-specific content.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM Graph Generator with Google Gemini API.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self.genai = None

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not provided. "
                "Set environment variable or pass api_key."
            )

        try:
            import google.generativeai as genai
            from google.generativeai.types import GenerationConfig

            genai.configure(api_key=self.api_key)
            self.genai = genai
            self.GenerationConfig = GenerationConfig
            self.client = genai.GenerativeModel("models/gemini-1.5-pro")

            print("[OK] LLM Graph Generator initialized (Gemini 1.5 Pro)")

        except ImportError:
            raise ImportError(
                "google-generativeai not installed.\n"
                "Install using: pip install google-generativeai"
            )

    # -----------------------------------------------------

    def generate_graph_with_ids(self, topic: str) -> Optional[str]:
        """
        Generate Mermaid flowchart syntax using Gemini.
        """

        prompt = f"""
Generate a Mermaid flowchart for the topic: "{topic}"

ABSOLUTE RULES (MUST FOLLOW):
1. DO NOT use generic academic sections such as:
   Introduction, Definition, Overview, Conclusion, Summary, Learning
2. DO NOT structure the diagram like an essay or presentation.
3. EVERY node must represent a REAL domain-specific entity, process, or operation
   related ONLY to the topic.
4. Node labels MUST contain technical/domain keywords.
   If a label could fit any subject, it is INVALID.
5. At least ONE decision node ({{Decision}}) is REQUIRED.
6. At least ONE storage/cylindrical node ((("Storage"))) is REQUIRED.
7. If the topic is a process or cycle, include a feedback or return arrow.

SYNTAX RULES:
- Start with: graph TD
- Node IDs: A, B, C, D, E, F...
- One arrow per line ONLY
- Shapes ONLY (no colors, no styles)
- Use:
  ([Start/End])
  ["Process"]
  {{Decision}}
  (("Storage"))
- Return ONLY valid Mermaid code
- No markdown blocks
- No explanations

Generate now.
"""


        try:
            response = self.client.generate_content(
                prompt,
                generation_config=self.GenerationConfig(
                    temperature=0.6,
                    max_output_tokens=2000,
                ),
            )

            code = response.text.strip()
            code = self._clean_mermaid_code(code)
            code = self._fix_mermaid_syntax(code)

            if not code.startswith("graph"):
                raise ValueError("Generated output is not valid Mermaid.")

            return code

        except Exception as e:
            print("[ERROR] Mermaid generation failed:", e)
            return None

    # -----------------------------------------------------

    def _clean_mermaid_code(self, code: str) -> str:
        """
        Remove markdown fences and trim.
        """
        code = code.strip()

        if code.startswith("```"):
            lines = code.splitlines()
            lines = [l for l in lines if not l.strip().startswith("```")]
            code = "\n".join(lines)

        return code.strip()

    # -----------------------------------------------------

    def _fix_mermaid_syntax(self, code: str) -> str:
        """
        Fix only SAFE Mermaid issues.
        No destructive rewriting.
        """
        fixed_lines = []

        for line in code.splitlines():
            line = line.rstrip()
            if not line or line.startswith("%%"):
                continue

            # Ensure graph TD stays
            if line.startswith("graph"):
                fixed_lines.append(line)
                continue

            # Fix chained arrows: A --> B --> C
            if line.count("-->") > 1:
                parts = [p.strip() for p in line.split("-->")]
                for i in range(len(parts) - 1):
                    left = self._extract_node_id(parts[i])
                    right = self._extract_node_id(parts[i + 1])
                    if left and right:
                        fixed_lines.append(f"{left} --> {right}")
                continue

            # Fix cylindrical mistakes: [("X")] → (("X"))
            line = re.sub(
                r'\[\(\("([^"]+)"\)\)\]',
                r'(("\1"))',
                line
            )

            # Fix decision nodes: {X} → {{X}}
            line = re.sub(
                r'([A-Z])\{([^{}"]+)\}',
                r'\1{{"\2"}}',
                line
            )

            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    # -----------------------------------------------------

    @staticmethod
    def _extract_node_id(text: str) -> Optional[str]:
        match = re.match(r'^([A-Z])', text)
        return match.group(1) if match else None

    # -----------------------------------------------------

    def is_available(self) -> bool:
        return self.client is not None


# =========================================================
# CLI Test
# =========================================================

if __name__ == "__main__":
    import sys

    api_key = os.getenv("GEMINI_API_KEY")
    if len(sys.argv) > 1:
        api_key = sys.argv[1]

    generator = LLMGraphGenerator(api_key=api_key)

    topic = input("Enter topic: ").strip() or "Photosynthesis Process"

    print("\n[INFO] Generating Mermaid diagram...\n")

    result = generator.generate_graph_with_ids(topic)

    if result:
        print("========== MERMAID CODE ==========")
        print(result)
        print("=================================")
    else:
        print("[ERROR] Generation failed")
