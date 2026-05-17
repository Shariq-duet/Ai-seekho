import os
import json
import time
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai

class LogEntry(BaseModel):
    log_id: str = Field(description="Unique ID in format MSG-XXXX, starting sequentially from MSG-8842")
    timestamp: str = Field(description="Timestamp of the message in format YYYY-MM-DDTHH:MM:SSZ. Infer from log or use a default if missing.")
    platform: str = Field(description="Platform the message was sent on, e.g. Discord, Reddit")
    username: str = Field(description="Username of the sender")
    category_tag: str = Field(description="Category tag: Bug_Report (for critical collision/physics issues) or General (for UI/Lore/Lag complaints)")
    message_text: str = Field(description="The actual message content")
    media_url: str | None = Field(description="URL of the media if present, else null", default=None)

class IngestedLogs(BaseModel):
    logs: list[LogEntry]

def run_ingestion(raw_text: str) -> list[dict]:
    print("Agent Observation: Received live text stream. Commencing parsing...")
    load_dotenv()
    
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    # Deferred initialization to prevent boot-crashes
    client = genai.Client()
    
    system_instruction = """
    You are the primary Ingestion Agent for our Challenge 1 workflow. 
    Your strict mandate is to parse unstructured natural language and transform it into a highly structured JSON array. 
    Extract the relevant player complaints along with any associated media URLs.
    If a message does not contain a video link, you must set the media_url to null.
    Infer the platform from the text if possible, or default to Discord. 
    Categorize the issues: use 'Bug_Report' exclusively for critical bugs and 'General' for UI complaints, lag, or other chatter.
    Map the extracted information perfectly to the schema.
    """

    prompt = f"Parse the following unstructured logs into the requested JSON schema:\n\n{raw_text}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IngestedLogs,
                system_instruction=system_instruction,
                temperature=0.0
            ),
        )
        
        response_data = json.loads(response.text)
        logs = response_data.get("logs", [])
        print(f"Successfully extracted {len(logs)} logs from the stream.")
        return logs
        
    except Exception as e:
        print(f"Agent Error: Failed to parse logs. Details: {e}")
        return []
if __name__ == "__main__":
    parse_logs()