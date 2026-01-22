from pathlib import Path
from agent import FlowchartAgent
import time

def main():
    topic = input("Enter any topic: ").strip()
    timestamp = int(time.time())

    
    output_path = Path(f"{topic.replace(' ', '_')}_{timestamp}.png")

    agent = FlowchartAgent()
    final_path = agent.generate_png(topic, output_path)

    print("\nFlowchart generated at:")
    print(final_path)

if __name__ == "__main__":
    main()
