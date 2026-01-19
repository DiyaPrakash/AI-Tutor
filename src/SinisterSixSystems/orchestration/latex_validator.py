import re
from langchain_google_genai import ChatGoogleGenerativeAI

def latex_validator_node(state):
    print("📍 [DEBUG] Entered Dynamic LaTeX Validator Node")
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    raw_latex = state.get("text_content", "")
    
    # 1. DYNAMIC PACKAGE MAPPING
    package_map = {
        "\\oiint": "\\usepackage{esint}",
        "\\oiiint": "\\usepackage{esint}",
        "\\physics": "\\usepackage{physics}",
        "\\ce{": "\\usepackage[version=4]{mhchem}",
        "\\cancel": "\\usepackage{cancel}",
        "axis": "\\usepackage{pgfplots}\\pgfplotsset{compat=1.18}",
        "\\begin{solution}": "\\newenvironment{solution}{\\par\\noindent\\textbf{Solution:}\\par}{\\medskip}"
    }

    # Auto-inject required tools based on content
    injections = []
    for command, code in package_map.items():
        if command in raw_latex and code not in raw_latex:
            injections.append(code)

    if injections:
        insertion_point = raw_latex.find("\\documentclass")
        if insertion_point != -1:
            end_of_line = raw_latex.find("\n", insertion_point) + 1
            raw_latex = raw_latex[:end_of_line] + "\n".join(injections) + "\n" + raw_latex[end_of_line:]

    # 2. UNIVERSAL CLEANUP PROMPT
    validation_prompt = f"""
    Fix this LaTeX for MiKTeX compatibility across ALL subjects:
    - SYMBOLS: If using advanced calculus/physics/chem, ensure the preamble has the packages.
    - ENVIRONMENTS: Ensure \\begin{{solution}} is properly defined if used.
    - PLACEMENT: Every figure MUST use [htbp] exactly.
    - CLEANUP: Remove stray 'htbp]' text and ensure scaling is 0.7\\textwidth.
    
    CONTENT: {raw_latex}
    """
    
    response = llm.invoke(validation_prompt)
    content = response.content

    # 3. FINAL REGEX SCRUB
    # Remove the stray 'htbp]' text you saw in your images
    content = re.sub(r'(?<!\[)htbp\]', '', content) 
    
    # Force correct figure syntax
    content = re.sub(r'\\begin{figure}\[?.*?\]?', r'\\begin{figure}[htbp]', content)
    content = content.replace("```latex", "").replace("```", "").strip()
    
    if "\\documentclass" in content:
        content = content[content.find("\\documentclass"):]

    return {"text_content": content}