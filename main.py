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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Now we will create clients, and we will set the API Key from .getenv() method
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
                        "You are a prescription OCR and risk-analysis system. "
                        "Analyze the prescription image and return structured data."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
Analyze this prescription image.

Extract only visibly readable text.
Identify medicines that can actually be read.
Do not invent missing information.

Return:
- OCR text
- detected medicines
- risk score from 0 to 100
- potential risks
- recommendations
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
                "type": "json_schema",
                "json_schema": {
                    "name": "prescription_analysis",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "ocr_text": {
                                "type": "string"
                            },
                            "medicines_detected": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "risk_score": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100
                            },
                            "risks": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "recommendations": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "required": [
                            "ocr_text",
                            "medicines_detected",
                            "risk_score",
                            "risks",
                            "recommendations"
                        ],
                        "additionalProperties": False
                    }
                }
            },

            temperature=0
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