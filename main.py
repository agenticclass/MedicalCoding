from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import json
from enum import Enum
from typing import Optional

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/test_data", StaticFiles(directory="test_data"), name="test_data")
templates = Jinja2Templates(directory="templates")

# Deepseek API configuration
DEEPSEEK_URL = "https://glhf.chat/api/openai/v1"
MODEL_NAME = "hf:deepseek-ai/DeepSeek-R1"
API_KEY = ""

class DocumentType(Enum):
    AUTHORIZATION = "authorization"
    MEDICAL_CODING = "medical_coding"
    CLAIM_ATTACHMENT = "claim_attachment"
    CLAIM_STATUS = "claim_status"

def detect_document_type(text: str) -> DocumentType:
    """Detect the type of document based on content analysis."""
    text_lower = text.lower()
    
    if "prior authorization" in text_lower or "auth" in text_lower:
        return DocumentType.AUTHORIZATION
    elif "claim status" in text_lower or "claim tracking" in text_lower:
        return DocumentType.CLAIM_STATUS
    elif "claim support" in text_lower or "supporting documentation" in text_lower:
        return DocumentType.CLAIM_ATTACHMENT
    else:
        return DocumentType.MEDICAL_CODING  # Default to medical coding

def get_analysis_prompt(doc_type: DocumentType, text: str) -> str:
    """Get the appropriate analysis prompt based on document type."""
    
    base_prompt = "You are an advanced healthcare automation assistant. "
    
    prompts = {
        DocumentType.AUTHORIZATION: base_prompt + """Analyze this prior authorization request and provide:
1. Authorization Recommendation:
   - Approval/Denial recommendation with confidence level
   - Supporting evidence from documentation
   - Missing information or documentation gaps

2. Medical Necessity Analysis:
   - Clinical criteria met/not met
   - Evidence from documentation
   - Additional documentation needed

3. Policy Compliance:
   - Relevant policy guidelines
   - Documentation requirements met/missing
   - Suggested improvements""",

        DocumentType.MEDICAL_CODING: base_prompt + """Analyze this clinical documentation and provide:
1. ICD-10 Codes:
   - List each applicable code with description
   - Provide confidence level (High/Medium/Low)
   - Include supporting quotes from documentation
   - Specify primary diagnosis and secondary diagnoses

2. CPT/HCPCS Codes:
   - List each applicable procedure code
   - Include confidence level and rationale
   - Link to specific documentation sections
   - Note any bundling considerations

3. Quality Measures Impact:
   - Identify relevant quality measures
   - Note documentation gaps affecting measures
   - Suggest documentation improvements

4. CMI Impact Analysis:
   - Identify codes affecting CMI
   - Note potential missed opportunities
   - Suggest queries if documentation is unclear""",

        DocumentType.CLAIM_ATTACHMENT: base_prompt + """Analyze this clinical documentation for claim support and provide:
1. Documentation Assessment:
   - Completeness evaluation
   - Missing elements identification
   - Quality of supporting evidence

2. Medical Necessity Validation:
   - Evidence of medical necessity
   - Clinical indicators present
   - Documentation gaps

3. Coding Support Analysis:
   - Documentation supporting assigned codes
   - Areas needing clarification
   - Additional documentation recommendations""",

        DocumentType.CLAIM_STATUS: base_prompt + """Analyze this claim status information and provide:
1. Status Assessment:
   - Current processing stage
   - Pending actions required
   - Timeline analysis

2. Documentation Requirements:
   - Missing documentation
   - Additional information needed
   - Submission recommendations

3. Next Steps:
   - Recommended actions
   - Priority items
   - Timeline considerations"""
    }
    
    return prompts[doc_type] + f"\n\nDocument Text:\n{text}"

async def get_analysis(text: str):
    """Get analysis for the provided document."""
    try:
        doc_type = detect_document_type(text)
        prompt = get_analysis_prompt(doc_type, text)
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(100)) as client:
            try:
                response = await client.post(DEEPSEEK_URL, json=data, headers=headers)
                response.raise_for_status()  # Raise exception for non-200 status codes
                result = response.json()
                return {
                    "type": doc_type.value,
                    "analysis": result
                }
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Network Error: {str(e)}")
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Invalid JSON response from API")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_documentation(
    request: Request,
    documentation: str = Form(...),
    doc_type: Optional[str] = Form(None)
):
    try:
        if not documentation.strip():
            raise HTTPException(status_code=400, detail="Documentation text cannat be empty")
            
        result = await get_analysis(documentation)
        return templates.TemplateResponse("result.html", {
            "request": request,
            "input": documentation,
            "result": result["analysis"],
            "doc_type": result["type"]
        })
    except HTTPException as e:
        return templates.TemplateResponse("result.html", {
            "request": request,
            "input": documentation,
            "error": e.detail,
            "doc_type": doc_type
        })
    except Exception as e:
        return templates.TemplateResponse("result.html", {
            "request": request,
            "input": documentation,
            "error": f"An unexpected error occurred: {str(e)}",
            "doc_type": doc_type
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
