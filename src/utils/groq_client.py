import os
import time
import requests
import re
from groq import Groq
from dotenv import load_dotenv

class MockChoiceMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.message = MockChoiceMessage(content)

class MockChatCompletion:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class GroqKeyRotator:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GroqKeyRotator, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_rotator()
        return cls._instance

    def _init_rotator(self):
        # We don't need key rotation or Ollama fallback since we use cascadeflow
        pass

    def execute_completion(self, messages, model="llama-3.3-70b-versatile", response_format=None, **kwargs):
        # We will use cascadeflow to route between a cheap model (qwen) and a smart model (llama)
        import asyncio
        from cascadeflow import CascadeAgent, ModelConfig
        import os
        import re

        # Define the Drafter (Fast/Cheap) and Verifier (Smart/Expensive)
        # Using Groq models natively
        agent = CascadeAgent(models=[
            ModelConfig(name="llama-3.1-8b-instant", provider="groq", cost=0.0001), # Drafter
            ModelConfig(name="llama-3.3-70b-versatile", provider="groq", cost=0.0005) # Verifier
        ])
        
        # If response_format is JSON, we ensure the prompt explicitly asks for it
        if response_format and response_format.get("type") == "json_object":
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] += " Output valid JSON only, no markdown formatting."

        # Run the cascade agent synchronously
        try:
            # We must run it in a new event loop if one is already running
            try:
                loop = asyncio.get_running_loop()
                # If there's a running loop, we can't use asyncio.run
                import threading
                result_container = []
                def run_in_thread():
                    result_container.append(asyncio.run(agent.run(messages=messages)))
                t = threading.Thread(target=run_in_thread)
                t.start()
                t.join()
                res = result_container[0]
            except RuntimeError:
                res = asyncio.run(agent.run(messages=messages))
                
            content = res.content
            
            # Print cost and savings to prove it's working
            print(f"[\033[92mCascadeFlow\033[0m] Model Used: {res.model_used}")
            print(f"[\033[92mCascadeFlow\033[0m] Cost Saved: ${res.cost_saved:.6f}")

            # Strip markdown if JSON was requested
            if response_format and response_format.get("type") == "json_object":
                content_clean = content.strip()
                if content_clean.startswith("```"):
                    match = re.search(r'```(?:json)?\s*(.*?)\s*```', content_clean, re.DOTALL | re.IGNORECASE)
                    if match:
                        content = match.group(1).strip()
                        
            return MockChatCompletion(content)
            
        except Exception as e:
            print(f"CascadeFlow execution failed: {e}")
            raise e

# Singleton instance
groq_rotator = GroqKeyRotator()
