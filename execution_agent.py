import sys
import os
import json
import requests
import time
from pydantic import BaseModel, Field
from google import genai
from dotenv import load_dotenv

# Set stdout to utf-8 to handle emojis in Discord markdown
sys.stdout.reconfigure(encoding='utf-8')

# --- Phase 3: Pydantic Schema ---
class IncidentAction(BaseModel):
    incident_title: str = Field(description="The title of the incident being addressed")
    severity: str = Field(description="Severity rating: 'Critical' or 'Minor'")
    implication_analysis: str = Field(description="Detailed analysis of the business and gameplay implications of this bug")
    simulated_code_patch: str = Field(description="A simulated code snippet (e.g., C#, Python, C++) that theoretically fixes the root cause of this specific bug.")
    jira_title: str = Field(description="A professional title for the Jira Bug Ticket.")
    jira_description_markdown: str = Field(description="A detailed Jira Bug Ticket description formatted in Markdown, including priority severity and list of video evidence URLs.")
    discord_announcement_markdown: str | None = Field(description="A Community Discord Announcement formatted in Markdown, apologizing for the issue. Null if severity is Minor.")

class ExecutionPlan(BaseModel):
    actions: list[IncidentAction] = Field(description="List of actions ranked by severity (Critical first, then Minor).")

# --- Phase 3: Execution Function ---
def generate_plan(incident_report: dict) -> ExecutionPlan:
    print("Agent Observation: Received structured IncidentReport. Initializing Execution Agent...")
    
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    client = genai.Client()
    
    report_json = json.dumps(incident_report, indent=2)

    system_instruction = (
        "You are the Execution Agent. Take the provided IncidentReport and generate an ExecutionPlan. "
        "1. Rank the incidents by severity (Critical first, then Minor). "
        "2. For each incident, provide an implication_analysis. "
        "3. Generate a Jira Ticket title and description. "
        "4. If the bug is Critical, generate a Discord Announcement. If Minor, leave discord_announcement_markdown as null. "
        "5. For every bug you analyze, you must act as a Senior Gameplay Programmer. Write a highly realistic, simulated code snippet that patches the core issue. For example, if it is a Unity physics clipping issue, write the C# script to fix the rigid body collision logic. If it is an economy exploit, write the server-side validation check. Return this snippet inside the simulated_code_patch field."
    )

    prompt = f"Here is the IncidentReport:\n\n{report_json}"

    print("Agent Action: Instructing Gemini API to generate Ranked Execution Plan...")
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExecutionPlan,
            system_instruction=system_instruction,
            temperature=0.7
        ),
    )
    
    try:
        plan_data = json.loads(response.text)
        plan = ExecutionPlan.model_validate(plan_data)
        print("Agent Reasoning: Successfully generated Execution Plan.")
        return plan
    except Exception as e:
        print(f"Agent Error: Failed to parse execution response. Details: {e}")
        return None

def execute_webhooks(plan: ExecutionPlan):
    jira_url = os.environ.get("JIRA_WEBHOOK_URL")
    jira_email = os.environ.get("JIRA_EMAIL")
    jira_token = os.environ.get("JIRA_API_TOKEN")
    jira_project_key = os.environ.get("JIRA_PROJECT_KEY")
    discord_url = os.environ.get("DISCORD_WEBHOOK_URL")

    total_actions = len(plan.actions)
    executed_jira = 0
    executed_discord = 0

    for action in plan.actions:
        print(f"\nProcessing [{action.severity}] Incident: {action.incident_title}")
        print(f"Implication Analysis: {action.implication_analysis}")
        
        # Post to Jira
        if jira_url and jira_email and jira_token and jira_project_key:
            print("Agent Action: Attempting to send Jira Ticket...")
            combined_description = action.jira_description_markdown + f"\n\n*Suggested AI Code Patch:*\n```\n{action.simulated_code_patch}\n```"

            try:
                jira_payload = {
                    "fields": {
                        "project": {"key": jira_project_key},
                        "summary": action.jira_title,
                        "issuetype": {"name": "Bug"},
                        "description": {
                            "type": "doc",
                            "version": 1,
                            "content": [{"type": "paragraph", "content": [{"type": "text", "text": combined_description}]}]
                        }
                    }
                }
                res = requests.post(jira_url, auth=(jira_email, jira_token), json=jira_payload, timeout=5)
                res.raise_for_status()
                executed_jira += 1
                print("Agent Observation: Jira Ticket posted successfully.")
            except requests.exceptions.RequestException as e:
                print(f"Agent Error: Jira POST request failed. Details: {e}")
        else:
            print("Agent Observation: Jira credentials missing. Skipping POST.")
        
        # Post to Discord conditionally
        if action.severity.lower() == "critical" and discord_url and action.discord_announcement_markdown:
            print("Agent Action: Attempting to send Discord Announcement for Critical bug...")
            try:
                payload = {"content": action.discord_announcement_markdown}
                res = requests.post(discord_url, json=payload, timeout=5)
                res.raise_for_status()
                executed_discord += 1
                print("Agent Observation: Discord Announcement posted successfully.")
            except requests.exceptions.RequestException as e:
                print(f"Agent Error: Discord POST request failed. Details: {e}")
        elif action.severity.lower() != "critical":
            print("Agent Reasoning: Bug is Minor. Skipping Discord announcement.")
        else:
             print("Agent Observation: Discord URL missing or markdown not provided. Skipping POST.")
            
        # Mandatory delay to prevent API rate-limiting during batch execution
        time.sleep(2)

    print("\n=======================================================")
    print("FINAL SYSTEM STATE SUMMARY:")
    print(f"Total Incidents Processed: {total_actions}")
    print(f"Jira Tickets Created: {executed_jira}")
    print(f"Discord Announcements Posted: {executed_discord}")
    print("Workflow Execution Complete.")
    print("=======================================================")

if __name__ == "__main__":
    load_dotenv()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(base_dir, "incident_report.json")
    
    if not os.path.exists(report_path):
        print(f"Error: {report_path} not found. Please run the clustering agent first.")
    else:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print("Starting Phase 3: Execution...")
        plan = generate_plan(data)
        if plan:
            execute_webhooks(plan)
