import os
import json
from pydantic import BaseModel, Field
from google import genai
from dotenv import load_dotenv

# Re-define LogEntry just for typing context
class LogEntry(BaseModel):
    log_id: str
    timestamp: str
    platform: str
    username: str
    category_tag: str
    message_text: str
    media_url: str | None = None

# --- Phase 2: Pydantic Schema ---
class IncidentReport(BaseModel):
    incident_title: str = Field(description="High-level title of the incident")
    affected_system: str = Field(description="The specific system, level, or mechanic affected")
    aggregated_description: str = Field(description="Synthesized description of the recurring symptoms")
    report_frequency: int = Field(description="Exact count of the specific bug occurrences in the provided batch")
    evidence_urls: list[str] = Field(description="List of all media URLs associated with the clustered bug reports")

class ClusteredInsights(BaseModel):
    incidents: list[IncidentReport]

# --- Phase 2: Clustering Function ---
# CRITICAL FIX: Renamed to run_clustering and accepts a list of dicts from server.py
def run_clustering(ingested_data: list[dict]) -> dict:
    print("Agent Observation: Scanning ingested logs for multiple distinct failure patterns...")
    
    load_dotenv()
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    client = genai.Client()
    
    # Convert the incoming list of dictionaries directly to a JSON string for the prompt
    logs_json = json.dumps(ingested_data, indent=2)

    system_instruction = (
        "Analyze the JSON array of logs. Filter out all irrelevant 'noise' (UI color complaints, lore discussions, lag). "
        "Identify ALL distinct, critical software bugs. For each distinct bug found, synthesize the related logs into a single IncidentReport. "
        "Return the full array of discovered incidents."
    )

    prompt = f"Here is the parsed JSON array of community logs for your analysis:\n\n{logs_json}"
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ClusteredInsights,
            system_instruction=system_instruction,
            temperature=0.0
        ),
    )
    
    try:
        # Parse the response and validate it against the Pydantic schema
        insights_data = json.loads(response.text)
        insights = ClusteredInsights.model_validate(insights_data)
        
        print(f"Agent Reasoning: Successfully isolated {len(insights.incidents)} distinct critical bugs from the noise.")
        for incident in insights.incidents:
            print(f"- {incident.incident_title}")
            
        # Return as a standard dictionary so server.py can seamlessly pass it to Phase 3
        return insights.model_dump()
    except Exception as e:
        print(f"Agent Error: Failed to parse clustering response. Details: {e}")
        return {}

# We omit the __main__ block here because Google Cloud Run does not use it. 
# The server.py file handles all execution now.