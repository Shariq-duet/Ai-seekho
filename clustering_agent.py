import os
import json
from pydantic import BaseModel, Field
from google import genai
from dotenv import load_dotenv

# Re-define LogEntry just for typing if needed, but since we are reading from JSON, 
# we can just pass the parsed Pydantic objects or dicts. We'll load the JSON and validate.
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
def cluster_logs(logs_array: list[LogEntry]) -> ClusteredInsights | None:
    print("Agent Observation: Scanning ingested logs for multiple distinct failure patterns...")
    
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    client = genai.Client()
    
    # Convert Pydantic objects back to a JSON string for the prompt context
    logs_json = json.dumps([log.model_dump() for log in logs_array], indent=2)

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
            
        return insights
    except Exception as e:
        print(f"Agent Error: Failed to parse clustering response. Details: {e}")
        return None

if __name__ == "__main__":
    load_dotenv()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_path = os.path.join(base_dir, "ingested_logs.json")
    
    if not os.path.exists(logs_path):
        print(f"Error: {logs_path} not found. Please run the ingestion agent first.")
    else:
        with open(logs_path, 'r', encoding='utf-8') as f:
            logs_data = json.load(f)
            
        logs_array = [LogEntry.model_validate(log) for log in logs_data]
        
        print("Starting Phase 2: Insight Clustering...")
        insights = cluster_logs(logs_array)
        
        if insights:
            print("\n--- FINAL CLUSTERED INSIGHTS ---")
            print(json.dumps(insights.model_dump(), indent=4))
            
            # Save the report
            report_path = os.path.join(base_dir, "incident_report.json")
            with open(report_path, 'w', encoding='utf-8') as rf:
                json.dump(insights.model_dump(), rf, indent=4)
            print(f"\nReport saved to {report_path}")
