import sys
import os
import asyncio
from agent.agent import XbotAgent
from dotenv import load_dotenv

load_dotenv()

async def main():
    """Main CLI entry point for Xbot AI Agent (Async)."""
    # Check for CLI arguments (for sub-agents)
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        try:
            agent = XbotAgent()
            print(f"[Sub-Agent] Running task: {task}")
            await agent.run(task)
            print("[Sub-Agent] Task complete.")
            return
        except Exception as e:
            print(f"[Sub-Agent] Error: {e}")
            sys.exit(1)

    print("=" * 30)
    print("Welcome to Xbot - Your Autonomous AI Agent")
    print("=" * 30)
    print("Type your instructions for the agent (e.g., 'Check my git status and list all python files')")
    print("Type 'exit' to quit.\n")
    
    try:
        agent = XbotAgent()
    except Exception as e:
        print(f"Failed to initialize Xbot: {e}")
        return
    
    while True:
        try:
            # We use loop.run_in_executor for non-blocking input if needed, 
            # but for a simple CLI, a standard input is fine since the 
            # agent.run(...) is where the heavy lifting happens.
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
                
            await agent.run(user_input)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n[System Error]: {str(e)}")

if __name__ == "__main__":
    # Dependency check
    try:
        import anthropic
        import dotenv
        import httpx
        import google.genai
    except ImportError as e:
        print(f"Missing dependency: {e}. Please run: pip install -r requirements.txt")
        sys.exit(1)
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
