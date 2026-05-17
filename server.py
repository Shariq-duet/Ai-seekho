import os
import json
import time
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze-upload")
async def analyze_upload_endpoint(file: UploadFile = File(...)):
    """Live Endpoint: Reads a single uploaded .txt file from the UI."""
    print("\n--- API: Received Upload. Triggering Phase 1 (Ingestion) ---")
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
        
    content = await file.read()
    injected_text = content.decode("utf-8")
    
    # Note: If the UI uploads a massive file, this might still hit the output token limit.
    # Advise the UI team to upload sample files, not 50MB database dumps.
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
        
    print("API Observation: ExecutionPlan generated. Returning payload to frontend.")
    return plan.model_dump()

@app.post("/analyze-local")
async def analyze_local_endpoint():
    """Fallback Endpoint: Reads from the local mock_discord_logs folder using Chunking."""
    print("\n--- API: Triggering Phase 1 (Sequential Local Ingestion) ---")
    
    log_dir = "mock_discord_logs"
    if not os.path.exists(log_dir):
        raise HTTPException(status_code=404, detail="Local log directory not found.")
        
    files = [f for f in os.listdir(log_dir) if f.endswith(".txt")]
    if not files:
         raise HTTPException(status_code=400, detail="Local log directory is empty.")

    master_logs_list = []

    # Process each file individually to strictly enforce token output limits
    for filename in files:
        filepath = os.path.join(log_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            file_text = f.read()
            
        print(f"API Action: Sending {filename} to Ingestion Agent...")
        file_logs = run_ingestion(file_text)
        
        if file_logs:
            master_logs_list.extend(file_logs)
            print(f"API Observation: Added {len(file_logs)} logs to the master list.")
        else:
            print(f"API Warning: Failed to parse {filename} or file was empty.")
            
        # Mandatory delay to prevent rate-limiting during the loop
        time.sleep(3)
            
    if not master_logs_list:
        raise HTTPException(status_code=500, detail="Phase 1 Ingestion completely failed to parse any local logs.")
        
    print(f"\nAPI Observation: Phase 1 Complete. {len(master_logs_list)} total logs extracted.")
    print("--- API: Triggering Phase 2 (Clustering) ---")
    
    insights_dict = run_clustering(master_logs_list)
    if not insights_dict or "incidents" not in insights_dict:
        raise HTTPException(status_code=500, detail="Phase 2 Clustering failed.")
        
    print("\n--- API: Triggering Phase 3 (Generation) ---")
    plan = generate_plan(insights_dict)
    if not plan:
        raise HTTPException(status_code=500, detail="Phase 3 Plan generation failed.")
        
    print("API Observation: ExecutionPlan generated from local data.")
    return plan.model_dump()

@app.post("/execute")
async def execute_endpoint(plan: ExecutionPlan):
    print("\n--- API: Human Approved! Triggering Phase 3 (Webhooks) ---")
    execute_webhooks(plan)
    return {"status": "success", "message": "Webhooks executed successfully."}