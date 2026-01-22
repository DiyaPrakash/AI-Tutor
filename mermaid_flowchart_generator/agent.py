from pathlib import Path
from mmdc import MermaidConverter
from llm_generator import LLMGraphGenerator
from mermaid_utils import validate_mermaid
import base64
import requests

class FlowchartAgent:
    def __init__(self, api_key=None):
        self.llm = LLMGraphGenerator(api_key)
        self.converter = MermaidConverter()

    def generate_png(self, topic: str, output_path: Path):
        code = self.llm.generate(topic)

        
        lines = [line.strip() for line in code.splitlines() if line.strip()]
        if not lines or not lines[0].startswith("graph TD"):
            lines.insert(0, "graph TD")

        
        if not any("-->" in line for line in lines):
            lines.append("A([Start]) --> B([End])")  

        code = "\n".join(lines)

        
        output_path.parent.mkdir(parents=True, exist_ok=True)

        success = False

        
        try:
            validate_mermaid(code)
            self.converter.to_png(code, output_file=output_path)

        
            if output_path.exists() and output_path.stat().st_size >= 500:
                success = True
            else:
                print("Local generation produced empty/missing file. Trying online fallback...")
        except Exception as e:
            print(f"Error generating PNG locally: {e}. Using fallback.")

        
        if not success:
            success = self._generate_via_ink(code, output_path)

        
        if not success:
            print("Complex graph generation failed. Generating simple fallback...")
            fallback_code = self._get_fallback_code(topic)
        
            success = self._generate_via_ink(fallback_code, output_path)

        return output_path

    def _generate_via_ink(self, code: str, output_path: Path) -> bool:
        """
        Generates PNG using mermaid.ink API.
        """
        try:
            graphbytes = code.encode("utf8")
            base64_bytes = base64.urlsafe_b64encode(graphbytes)
            base64_string = base64_bytes.decode("ascii")
        
            url = f"https://mermaid.ink/img/{base64_string}?bgColor=FFFFFF"
            
            print("Requesting PNG from mermaid.ink...")
            response = requests.get(url)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print("Fallback generation successful.")
                return True
            else:
                print(f"Mermaid.ink failed with status {response.status_code}")
                return False
        except Exception as e:
            print(f"Mermaid.ink exception: {e}")
            return False

    def _get_fallback_code(self, topic: str) -> str:
        return f"""
graph TD
    A([Start: {topic}]) --> B["Core Step"]
    B --> C{{Decision}}
    C --> D["Next Step"]
    D --> E(("Storage"))
    E --> B
"""
