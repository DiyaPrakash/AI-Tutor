import os
from langchain_google_genai import ChatGoogleGenerativeAI
from src.SinisterSixSystems.agent_lightning import LightningStore

# Initialize the persistent memory store
store = LightningStore(path="./artifacts/agent_memory")

def lightning_optimizer_node(state):
    print("⚡ [DEBUG] Accessing Agent Lightning Memory (Strict Mode)...")
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)
    
    current_content = state.get("text_content", "")
    original_task = state.get("user_input", "")
    current_score = state.get("score", 0)

    # Experience Retrieval: Check for high-reward previous solutions
    best_experience = store.get_best_trajectory(original_task)
    reference_hint = ""
    if best_experience and best_experience.get('reward', 0) >= 9:
        print(f"📖 [INFO] Loading high-reward reference (Score: {best_experience['reward']})")
        reference_hint = f"REFERENCE FROM MEMORY:\n{best_experience['content']}"

    # Reinforcement Learning Prompt with Strict Constraints
    lightning_prompt = f"""
    OPTIMIZATION TASK: Your previous attempt scored {current_score}/10 for efficiency.
    
    ORIGINAL GOAL: {original_task}
    
    CRITICAL CONSTRAINT: 
    - DO NOT introduce ANY new LaTeX packages (e.g., esint, physics, cancel, mhchem).
    - Use ONLY the packages already defined in the preamble (amsmath, amssymb, pgfplots).
    - If you need advanced symbols like closed surface integrals, use standard \\oint symbols or express them using basic amsmath notation.
    
    IMPROVEMENT GOALS:
    - Enhance conceptual depth and pedagogical flow.
    - Ensure the 3D surface plot is clearly labeled and uses correct PGFPlots syntax.
    - Fix the difficulty scaling for exercises (Easy, Medium, Hard).
    
    {reference_hint}
    
    PREVIOUS DRAFT: {current_content}
    
    Provide the final, optimized LaTeX document. Include only the LaTeX code.
    """
    
    response = llm.invoke(lightning_prompt)
    optimized_content = response.content.replace("```latex", "").replace("```", "").strip()

    # Save the trajectory for future runs
    store.save_trajectory(original_task, optimized_content, reward=8) 
    
    print("✅ Optimization complete within environment constraints.")
    return {"text_content": optimized_content, "retry_count": 1}