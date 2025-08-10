#!/usr/bin/env python3
import os
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

async def test_llm():
    try:
        key = os.environ.get('EMERGENT_LLM_KEY')
        print(f"Using key: {key[:15]}...")
        
        # Simple initialization without specifying model
        chat = LlmChat(
            api_key=key,
            session_id="test-session",
            system_message="You are a helpful assistant."
        )
        
        # Try different model configurations
        try:
            chat = chat.with_model("openai", "gpt-4o-mini")
            print("Model set successfully")
        except Exception as e:
            print(f"Model setting error: {e}")
            # Continue without model specification
        
        user_message = UserMessage(text="Say hello")
        
        print("Sending message...")
        response = await chat.send_message(user_message)
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm())