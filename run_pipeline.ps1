$ErrorActionPreference = "Stop"

Write-Output "Starting Phase 1: Ingestion..."
python -u ingestion_agent.py

Write-Output "Starting Phase 2: Clustering..."
python -u clustering_agent.py

Write-Output "Starting Phase 3: Execution..."
python -u execution_agent.py

Write-Output "Pipeline Complete!"
