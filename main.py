from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Deepseek API configuration
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"
API_KEY = "sk-98dba0799f2a45d09a2b688a95f62db9"

async def get_coding_suggestions(text: str):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""You are a medical coding assistant. Analyze the following medical documentation and provide:
1. ICD-10 codes
2. CPT codes
3. HCPCS codes
4. Code descriptions
5. Coding rationale

Medical Documentation:
{text}"""

    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_URL, json=data, headers=headers)
        return response.json()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_documentation(request: Request, documentation: str = Form(...)):
    result = await get_coding_suggestions(documentation)
    return templates.TemplateResponse("result.html", {
        "request": request,
        "input": documentation,
        "result": result
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
