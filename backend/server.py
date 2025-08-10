from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime
import asyncio
import json

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

async def generate_enhanced_prompt(simple_command: str) -> tuple:
    """
    Generate detailed prompts from simple commands
    This is a fallback implementation that creates professional prompts
    """
    # Enhanced prompt templates based on common patterns
    structured_template = f"""# Context
You need to {simple_command.lower()}. This task requires careful attention to detail and professional execution.

# Task Description
{simple_command}

# Requirements
- Maintain high quality standards
- Follow best practices
- Provide comprehensive output
- Consider your target audience
- Ensure clarity and effectiveness

# Output Format
- Structure your response logically
- Use clear headings and sections
- Provide specific examples where relevant
- Include actionable steps or guidelines

# Guidelines
- Be thorough but concise
- Use professional language
- Consider different perspectives
- Validate your approach
- Ensure practical applicability

# Success Criteria
- Meets all specified requirements
- Demonstrates expertise
- Provides value to the user
- Is ready for immediate use"""

    system_template = f"""You are an expert professional assistant. Your task is to {simple_command.lower()}.

Key Instructions:
- Approach this task with expertise and attention to detail
- Provide comprehensive, high-quality output
- Follow industry best practices
- Structure your response clearly and logically
- Include specific, actionable guidance
- Consider the end user's needs and context
- Ensure your response is immediately usable
- Maintain professional standards throughout

Execute this task thoroughly and professionally."""

    return structured_template, system_template

@app.get("/")
async def root():
    return {"message": "AI Prompt Engineer API is running"}

@app.post("/api/generate-prompt")
async def generate_prompt(request: PromptRequest):
    try:
        if not request.command.strip():
            raise HTTPException(status_code=400, detail="Command cannot be empty")
        
        print(f"Generating prompt for command: {request.command}")
        
        # Generate detailed prompts
        structured_prompt, system_prompt = await generate_enhanced_prompt(request.command)
        
        # Create prompt record
        prompt_id = str(uuid.uuid4())
        prompt_record = {
            "id": prompt_id,
            "command": request.command,
            "structured_prompt": structured_prompt,
            "system_prompt": system_prompt,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save to database
        await prompts_collection.insert_one(prompt_record)
        
        print(f"Successfully generated and saved prompt with ID: {prompt_id}")
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
    return {
        "status": "healthy", 
        "llm_key_configured": bool(EMERGENT_LLM_KEY),
        "version": "v1.0-fallback"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)