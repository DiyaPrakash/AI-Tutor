from langchain_google_genai import ChatGoogleGenerativeAI

def scoring_node(state):
    print(f"📍 [DEBUG] Entered Scoring Agent (Attempt {state.get('retry_count', 0) + 1})")
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    
    content = state.get("text_content", "")
    
    scoring_prompt = f"""
    Evaluate this academic lesson for 'Efficiency':
    1. Depth: Does the concept explanation provide enough detail for a student?
    2. Scaling: Are the Hard questions significantly more difficult than the Easy ones?
    3. Integration: Does the 3D graph (if present) actually help explain the math?

    Give a score from 1 to 10. 
    Return ONLY the number.
    CONTENT: {content}
    """
    
    response = llm.invoke(scoring_prompt)
    try:
        score = int(response.content.strip())
    except:
        score = 5 # Default if LLM gives non-numeric response
        
    return {"score": score}