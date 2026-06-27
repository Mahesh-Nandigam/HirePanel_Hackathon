import asyncio
from cascadeflow import CascadeAgent, ModelConfig
import os

from dotenv import load_dotenv
load_dotenv()

os.environ["GROQ_API_KEY"] = os.environ.get("GROQ_API_KEY_1", os.environ.get("GROQ_API_KEY", ""))

async def main():
    print("Testing CascadeAgent...")
    # The hackathon doc says: openai/gpt-oss-120b and qwen/qwen3-32b but Groq models are different names.
    # Let's try the actual Groq models: 'qwen-2.5-32b' and 'llama-3.3-70b-versatile'
    agent = CascadeAgent(models=[
        ModelConfig(name="qwen-2.5-32b", provider="groq", cost=0.0001),
        ModelConfig(name="llama-3.3-70b-versatile", provider="groq", cost=0.0005)
    ])
    
    # Try passing messages list
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello world in JSON format like {\"greeting\": \"...\"}"}
    ]
    
    try:
        # Check if we can pass response_format to run?
        # If not, we can just ask for json in prompt.
        res = await agent.run(messages)
        print("Success with messages list!")
        print("Model used:", res.model_used)
        print(res.content)
    except Exception as e:
        print(f"Failed with messages: {e}")
        
asyncio.run(main())
