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

def parse_logs():
    load_dotenv()
    
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    client = genai.Client()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "mock_discord_logs")
    
    if not os.path.exists(data_dir):
        print(f"Error: Directory {data_dir} not found.")
        return

    files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
    print(f"Agent Observation: Located {len(files)} files in the target directory. Commencing batch parsing...")
    
    system_instruction = """
    You are the primary Ingestion Agent for our Challenge 1 workflow. 
    Your strict mandate is to parse unstructured natural language and transform it into a highly structured JSON array. 
    Extract the relevant player complaints along with any associated media URLs.
    If a message does not contain a video link, you must set the media_url to null.
    Infer the platform from the filename if possible, or default to Discord. 
    Categorize the issues: use 'Bug_Report' exclusively for critical bugs and 'General' for UI complaints, lag, or other chatter.
    Map the extracted information perfectly to the schema.
    """

    master_logs_array = []
    batch_size = 10

    for i in range(0, len(files), batch_size):
        batch_files = files[i:i + batch_size]
        print(f"\nProcessing batch {i // batch_size + 1} of {(len(files) + batch_size - 1) // batch_size}...")
        
        combined_raw_text = ""
        for filename in batch_files:
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                combined_raw_text += f"\n--- File: {filename} ---\n"
                combined_raw_text += f.read()

        prompt = f"Parse the following unstructured logs into the requested JSON schema:\n\n{combined_raw_text}"
        
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
            batch_logs = response_data.get("logs", [])
            master_logs_array.extend(batch_logs)
            print(f"Successfully extracted {len(batch_logs)} logs from this batch.")
            
        except Exception as e:
            print(f"Agent Error: Failed to parse batch starting at index {i}. Details: {e}")
            
        # Mandatory delay to respect API rate limits
        time.sleep(4)

    output_file = os.path.join(base_dir, "ingested_logs.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(master_logs_array, f, indent=4)

    print(f"\nAgent Conclusion: Successfully generated and parsed a total of {len(master_logs_array)} logs into {output_file}")

if __name__ == "__main__":
    parse_logs()