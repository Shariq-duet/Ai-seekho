import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import functions from existing phase scripts
from ingestion_agent import run_ingestion
from clustering_agent import run_clustering
from execution_agent import generate_plan, execute_webhooks, ExecutionPlan

# Load environment variables
load_dotenv()

app = FastAPI(title="3-Phase Agentic Workflow API")

# Configure CORS to allow all origins for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze-upload")
async def analyze_upload_endpoint(file: UploadFile = File(...)):
    print("\n--- API: Received Upload. Triggering Phase 1 (Ingestion) ---")
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
        
    content = await file.read()
    injected_text = content.decode("utf-8")
    
    logs_list = run_ingestion(injected_text)
    if not logs_list:
        raise HTTPException(status_code=500, detail="Phase 1 Ingestion failed to parse logs.")
        
    print("\n--- API: Triggering Phase 2 (Clustering) ---")
    insights_dict = run_clustering(logs_list)
    if not insights_dict or "incidents" not in insights_dict:
        raise HTTPException(status_code=500, detail="Phase 2 Clustering failed to generate insights.")
        
    print("\n--- API: Triggering Phase 3 (Generation) ---")
    plan = generate_plan(insights_dict)
    
    if not plan:
        raise HTTPException(status_code=500, detail="Phase 3 Plan generation failed.")
        
    print("API Observation: ExecutionPlan generated. Returning payload to frontend for approval.")
    return plan.model_dump()

@app.post("/analyze-local")
async def analyze_local_endpoint():
    print("\n--- API: Received Local Request. Triggering Phase 1 (Ingestion) ---")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "mock_discord_logs")
    
    if not os.path.exists(data_dir) or not os.path.isdir(data_dir):
        raise HTTPException(status_code=404, detail="mock_discord_logs directory not found.")
        
    files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
    if not files:
        raise HTTPException(status_code=404, detail="No .txt files found in mock_discord_logs directory.")
        
    combined_raw_text = ""
    for filename in files:
        filepath = os.path.join(data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            combined_raw_text += f"\n--- File: {filename} ---\n"
            combined_raw_text += f.read()
            
    logs_list = run_ingestion(combined_raw_text)
    if not logs_list:
        raise HTTPException(status_code=500, detail="Phase 1 Ingestion failed to parse logs.")
        
    print("\n--- API: Triggering Phase 2 (Clustering) ---")
    insights_dict = run_clustering(logs_list)
    if not insights_dict or "incidents" not in insights_dict:
        raise HTTPException(status_code=500, detail="Phase 2 Clustering failed to generate insights.")
        
    print("\n--- API: Triggering Phase 3 (Generation) ---")
    plan = generate_plan(insights_dict)
    
    if not plan:
        raise HTTPException(status_code=500, detail="Phase 3 Plan generation failed.")
        
    print("API Observation: ExecutionPlan generated. Returning payload to frontend for approval.")
    return plan.model_dump()

@app.post("/execute")
async def execute_endpoint(plan: ExecutionPlan):
    print("\n--- API: Human Approved! Triggering Phase 3 (Webhooks) ---")
    execute_webhooks(plan)
    return {"status": "success", "message": "Webhooks executed successfully."}

if __name__ == "__main__":
    import uvicorn
    # Run server locally
    uvicorn.run(app, host="0.0.0.0", port=8000)
