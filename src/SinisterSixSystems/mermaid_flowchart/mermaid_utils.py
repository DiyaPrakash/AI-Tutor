import re

def sanitize_mermaid(code: str) -> str:
    """
    Cleans up Mermaid code from the LLM:
    - Removes empty lines
    - Strips whitespace
    - Removes edge labels |label|
    - Ignores style lines (style / classDef)
    """
    lines = []
    for line in code.splitlines():
        line = line.strip()
        if not line:
            continue
        
        if line.startswith("```"):
            continue
        
        line = re.sub(r'\|[^|]+\|', '', line)
        
        if line.startswith(("style ", "classDef ")):
            continue
        lines.append(line)
    return "\n".join(lines)


def validate_mermaid(code: str):
    """
    Validates sanitized Mermaid code.
    Ensures:
    - First meaningful line is 'graph TD'
    - At least one arrow exists
    """
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    
    if not lines:
        raise ValueError("Mermaid code is empty")
    
    if not lines[0].startswith("graph TD"):
        raise ValueError("Mermaid must start with graph TD")
    
    if not any("-->" in line for line in lines):
        raise ValueError("Mermaid must contain arrows")
