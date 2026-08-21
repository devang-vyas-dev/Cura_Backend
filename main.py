import os
import uuid
import json
import base64
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client
from groq import Groq

load_dotenv()
# The Line below is used to Initialize the FastApi app
app = FastAPI(title="Cura AI: A Prescription Scanner and Risk Analyzer")

# This is the Main code that will help in connecting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cura-ai-beta.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Now we will create clients, and we will set the API Key from .getenv() method
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

print("SUPABASE_URL:", SUPABASE_URL)
print("GROQ configured:", bool(GROQ_API_KEY))

# Create clients only if keys exist, otherwise None
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)

def image_to_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode('utf-8')

@app.get("/")
async def home():
    return {
        "status": "Backend Running Perfectly",
        "docs": "docs are accessible at /docs",
    }

@app.post("/api/v1/analyze-prescription")
async def analyze_document(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        base64_image = image_to_base64(file_bytes)

        mime_type = file.content_type or "image/jpeg"

        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.6-27b",

            messages=[
            {
                "role": "system",
                "content": (
                    "You are a prescription OCR and analysis system. "
                    "Return ONLY valid JSON. "
                    "Do not use markdown. "
                    "Do not add explanations outside the JSON."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        Analyze the prescription image.
                        Rules:
                        1. Extract only text that is visibly readable.
                        2. Never guess or invent medicine names.
                        3. Include only medicines that can actually be read.
                        4. If something cannot be read, omit it.
                        5. risk_score must be an integer from 0 to 100.
                        6. risks must be an array of strings.
                        7. recommendations must be an array of strings.
                        8. Return ONLY the JSON object.
                    Use exactly this structure:
                        {
                            "ocr_text": "string",
                            "medicines_detected": ["string"],
                            "risk_score": 0,
                            "risks": ["string"],
                            "recommendations": ["string"]
                        }
                        """
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    response_format={
        "type": "json_object"
    },
    temperature=0,
    max_tokens=1200,
    reasoning_effort="none"
)
        raw_content = completion.choices[0].message.content
        print("MODEL OUTPUT:", repr(raw_content))
        result = json.loads(raw_content)
        doc_id = str(uuid.uuid4())
        final_data = {
            "id": doc_id,
            "file_name": file.filename or "unknown",
            "ocr_text": result["ocr_text"],
            "medicines_detected": result["medicines_detected"],
            "risk_score": result["risk_score"],
            "risks": result["risks"],
            "recommendations": result["recommendations"]
        }
        supabase.table("prescriptions").insert(final_data).execute()
        return final_data
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )