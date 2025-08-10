from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage
import asyncio

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.prompt_engineer_db
prompts_collection = db.prompts

# LLM setup
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

class PromptRequest(BaseModel):
    command: str

class PromptResponse(BaseModel):
    id: str
    command: str
    structured_prompt: str
    system_prompt: str
    created_at: str

# Initialize LLM chat
def get_llm_chat():
    return LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id="prompt-engineer-session",
        system_message="""You are a world-class prompt engineer. Your task is to transform simple, single-line commands into detailed, comprehensive prompts that can be used effectively with other AI agents.

When given a simple command, you must create TWO versions:
1. STRUCTURED_PROMPT: A well-organized prompt with clear sections (Context, Task, Format, Guidelines, etc.)
2. SYSTEM_PROMPT: A technical system message format suitable for AI models

Guidelines for prompt engineering:
- Be specific and detailed
- Include context and background
- Specify desired output format
- Add relevant constraints and guidelines
- Include examples when helpful
- Consider edge cases
- Make prompts clear and unambiguous
- Ensure prompts are actionable

Response format:
STRUCTURED_PROMPT:
[Detailed structured prompt with sections]

SYSTEM_PROMPT:
[Technical system message format]"""
    ).with_model("openai", "gpt-4o-mini")

@app.get("/")
async def root():
    return {"message": "AI Prompt Engineer API is running"}

@app.post("/api/generate-prompt")
async def generate_prompt(request: PromptRequest):
    try:
        if not request.command.strip():
            raise HTTPException(status_code=400, detail="Command cannot be empty")
        
        # Generate detailed prompt using LLM
        chat = get_llm_chat()
        user_message = UserMessage(
            text=f"Transform this simple command into detailed prompts: '{request.command}'"
        )
        
        response = await chat.send_message(user_message)
        print(f"LLM Response type: {type(response)}")
        print(f"LLM Response: {response}")
        llm_output = str(response).strip()
        
        # Parse the response to extract structured and system prompts
        parts = llm_output.split("SYSTEM_PROMPT:")
        if len(parts) >= 2:
            structured_part = parts[0].replace("STRUCTURED_PROMPT:", "").strip()
            system_part = parts[1].strip()
        else:
            # Fallback parsing
            structured_part = llm_output
            system_part = f"You are a helpful AI assistant. {llm_output}"
        
        # Create prompt record
        prompt_id = str(uuid.uuid4())
        prompt_record = {
            "id": prompt_id,
            "command": request.command,
            "structured_prompt": structured_part,
            "system_prompt": system_part,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save to database
        await prompts_collection.insert_one(prompt_record)
        
        return PromptResponse(**prompt_record)
        
    except Exception as e:
        print(f"Error generating prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate prompt: {str(e)}")

@app.get("/api/prompts/{prompt_id}")
async def get_prompt(prompt_id: str):
    try:
        prompt = await prompts_collection.find_one({"id": prompt_id})
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        # Remove MongoDB _id field
        prompt.pop("_id", None)
        return prompt
        
    except Exception as e:
        print(f"Error fetching prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch prompt: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "llm_key_configured": bool(EMERGENT_LLM_KEY)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)