from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from demo_pipeline import analyze_resume  # import your existing function

app = FastAPI()

# Allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_resume_api(file: UploadFile = File(...)):
    content = await file.read()
    results = analyze_resume(content)  # This should return structured data
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
