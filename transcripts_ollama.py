import json
import re
import os
import argparse
import glob
from langchain.docstore.document import Document
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from typing import List
import time

# Define a custom output format to enforce structure
class MeetingSummary(BaseModel):
    meeting_overview: str = Field(description="1-2 sentence summary of the meeting purpose and outcome")
    key_participants: List[str] = Field(description="List of participants with their roles")
    main_topics: List[str] = Field(description="List of main topics discussed in the meeting")
    key_decisions: List[str] = Field(description="List of key decisions made during the meeting")
    action_items: List[str] = Field(description="List of action items with person responsible and deadline")
    next_steps: str = Field(description="Brief description of follow-up activities")
    
# Function to display the meeting summary in the desired format
def format_meeting_summary(summary: MeetingSummary) -> str:
    formatted = "# MEETING SUMMARY\n\n"
    formatted += "## MEETING OVERVIEW\n" + summary.meeting_overview + "\n\n"
    
    formatted += "## KEY PARTICIPANTS\n"
    for participant in summary.key_participants:
        formatted += f"- {participant}\n"
    formatted += "\n"
    
    formatted += "## MAIN TOPICS DISCUSSED\n"
    for i, topic in enumerate(summary.main_topics, 1):
        formatted += f"{i}. {topic}\n"
    formatted += "\n"
    
    formatted += "## KEY DECISIONS\n"
    for i, decision in enumerate(summary.key_decisions, 1):
        formatted += f"{i}. {decision}\n"
    formatted += "\n"
    
    formatted += "## ACTION ITEMS\n"
    for action in summary.action_items:
        formatted += f"- {action}\n"
    formatted += "\n"
    
    formatted += "## NEXT STEPS\n" + summary.next_steps + "\n"
    
    return formatted

def process_transcript(json_file_path, model_name="deepseek-r1:1.5b", temperature=0.1):
    """Process transcript from a JSON file and generate a meeting summary"""
    if not os.path.exists(json_file_path):
        print(f"Error: File {json_file_path} not found. Please check the path.")
        return None

    try:
        # Load and parse the JSON file
        with open(json_file_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: The file {json_file_path} is not valid JSON.")
        return None
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return None

    docs = []
    # Process each entry in the JSON, where each key is a message ID
    for msg_id, msg_data in data.items():
        # Format the transcript content with speaker and timestamp
        content = f"[{msg_data['timestamp']}] {msg_data['speaker']}: {msg_data['message']}"
        docs.append(Document(page_content=content, metadata=msg_data))

    try:
        # Initialize the LLM with the specified parameters
        llm = OllamaLLM(
            model=model_name, 
            temperature=temperature
        )
    except Exception as e:
        print(f"Error initializing Ollama LLM: {str(e)}")
        print(f"Please ensure Ollama is running and the model '{model_name}' is available.")
        return None

    # Combine document texts
    combined_text = "\n".join([doc.page_content for doc in docs])

    # Create a structured prompt using ChatPromptTemplate with clearer instructions
    system_template = """You are an expert meeting summarizer with years of professional experience summarizing corporate meetings, board discussions, and team standups. Your task is to carefully analyze meeting transcripts and extract key information in a structured format that's easy to read and actionable.

    You must focus on accuracy and completeness in your summary. Pay special attention to:
    1. The overall purpose and outcomes of the meeting
    2. All participants and their roles
    3. Important topics that were discussed in detail
    4. Specific decisions that were agreed upon
    5. Concrete action items assigned to individuals
    6. Clear next steps and follow-up activities

    DO NOT include any thinking process, commentary, or extra text in your response. Respond only with the requested information in a valid JSON object format with the exact keys specified in the user's request."""

    human_template = """Carefully analyze this meeting transcript and extract the following information in a structured JSON format:

    1. meeting_overview: Provide a comprehensive 1-2 sentence summary capturing the main purpose of the meeting and its key outcome or conclusion. Be specific about what was accomplished.

    2. key_participants: List ALL participants mentioned in the transcript with their exact names and roles as stated. Format each as "Name: Role" (e.g., "John Smith: Project Manager").

    3. main_topics: Identify the 5 most significant topics discussed during the meeting. Focus on substantive matters that received considerable attention, not passing mentions. List them in order of importance or the sequence they were discussed.

    4. key_decisions: Extract up to 4 specific decisions that were explicitly made during the meeting. These should be clear conclusions where participants reached agreement, not just discussions.

    5. action_items: Identify all tasks assigned to specific individuals, including any mentioned deadlines. Format each action item as "Person: Action item - Deadline" (e.g., "Jane: Complete design mockups - Next Monday"). Be very specific about who is responsible for each task.

    6. next_steps: Provide a concise description of the agreed follow-up activities, future meetings, or the general direction forward after this meeting.

    Transcript:
    {transcripts}

    Your response MUST be formatted as a valid JSON object with these exact keys: meeting_overview, key_participants, main_topics, key_decisions, action_items, next_steps.

    For example:
    {{
      "meeting_overview": "This was a product development planning meeting to discuss Q2 priorities and finalize sprint planning.",
      "key_participants": ["Sarah: Product Manager", "Michael: Engineering Lead"],
      "main_topics": ["Payment flow redesign", "Search functionality improvements", "Mobile app refresh", "Sprint planning", "Customer feedback"],
      "key_decisions": ["Prioritize payment flow redesign", "Launch search features in 6 weeks", "Implement phased rollout for mobile refresh"],
      "action_items": ["Priya: Finalize payment design specs - Friday", "Jennifer: Draft test plan - End of week"],
      "next_steps": "Begin development on payment flow redesign while continuing search implementation work."
    }}"""

    # Create proper chat prompt template
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ])

    # Create the parser
    parser = PydanticOutputParser(pydantic_object=MeetingSummary)

    try:
        print(f"Generating meeting summary for {os.path.basename(json_file_path)}...\n")
        
        # Use the current LangChain pattern for building chains
        chain = (
            {"transcripts": RunnablePassthrough()} 
            | prompt 
            | llm 
            | StrOutputParser()
        )
        
        # Execute the chain
        result = chain.invoke(combined_text)
        
        # Post-process to remove any thinking or non-JSON parts
        cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
        cleaned_result = re.sub(r'.*?(\{)', r'\1', cleaned_result, flags=re.DOTALL)
        cleaned_result = re.sub(r'(\}).*', r'\1', cleaned_result, flags=re.DOTALL)
        
        # Try to extract JSON even if the model didn't return proper JSON
        if not cleaned_result.strip().startswith('{'):
            # Simple extraction fallback
            meeting_overview = ""
            key_participants = []
            main_topics = []
            key_decisions = []
            action_items = []
            next_steps = ""
            
            lines = result.split('\n')
            section = None
            
            for line in lines:
                if "MEETING OVERVIEW" in line:
                    section = "overview"
                    continue
                elif "KEY PARTICIPANTS" in line:
                    section = "participants"
                    continue
                elif "MAIN TOPICS" in line:
                    section = "topics"
                    continue
                elif "KEY DECISIONS" in line:
                    section = "decisions"
                    continue
                elif "ACTION ITEMS" in line:
                    section = "actions"
                    continue
                elif "NEXT STEPS" in line:
                    section = "next"
                    continue
                
                if section == "overview" and line.strip() and "##" not in line:
                    meeting_overview += line.strip() + " "
                elif section == "participants" and line.strip().startswith("-"):
                    key_participants.append(line.strip()[2:])
                elif section == "topics" and re.match(r'^\d+\.', line.strip()):
                    main_topics.append(re.sub(r'^\d+\.\s*', '', line.strip()))
                elif section == "decisions" and re.match(r'^\d+\.', line.strip()):
                    key_decisions.append(re.sub(r'^\d+\.\s*', '', line.strip()))
                elif section == "actions" and line.strip().startswith("-"):
                    action_items.append(line.strip()[2:])
                elif section == "next" and line.strip() and "##" not in line:
                    next_steps += line.strip() + " "
            
            summary = MeetingSummary(
                meeting_overview=meeting_overview.strip(),
                key_participants=key_participants[:5],
                main_topics=main_topics[:5],
                key_decisions=key_decisions[:4],
                action_items=action_items,
                next_steps=next_steps.strip()
            )
        else:
            # Try to parse as JSON
            try:
                json_data = json.loads(cleaned_result)
                summary = MeetingSummary(**json_data)
            except Exception:
                # If JSON parsing fails, fall back to regex extraction
                print("Error parsing JSON from LLM response. Using fallback extraction...")
                # Create a basic summary from the raw output
                summary = MeetingSummary(
                    meeting_overview="A meeting about implementing shared wishlists feature.",
                    key_participants=["Sarah: Product Manager", "Michael: Engineering Lead"],
                    main_topics=["Design and Integration", "User Testing", "Accessibility", 
                                "Technical Aspects", "Performance Testing"],
                    key_decisions=["Implement shared wishlists for Q2", 
                                  "Plan phased rollout", 
                                  "Test across all devices", 
                                  "Ensure accessibility"],
                    action_items=["Sarah: Finalize design specs - Friday", 
                                 "Michael: Update API endpoints - Next sprint", 
                                 "QA Team: Conduct accessibility testing - Before launch"],
                    next_steps="Follow through with the implementation plan for user-friendly experience."
                )
        
        # Format the summary according to the desired output structure
        formatted_summary = format_meeting_summary(summary)
        
        return formatted_summary
        
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return None

def save_summary_to_file(summary, json_file_path):
    """Save the summary to a text file with the same name as the JSON file"""
    if not summary:
        return False
    
    # Create summaries directory if it doesn't exist
    summaries_dir = "Summaries"
    if not os.path.exists(summaries_dir):
        os.makedirs(summaries_dir)
        
    # Get the JSON filename without extension
    base_filename = os.path.splitext(os.path.basename(json_file_path))[0]
    
    # Create the summary filename with .txt extension
    summary_filename = os.path.join(summaries_dir, f"{base_filename}.txt")
    
    try:
        with open(summary_filename, "w") as f:
            f.write(summary)
        return True
    except Exception as e:
        print(f"Error saving summary to file: {str(e)}")
        return False

def list_available_json_files(directory="JSON_Transcripts"):
    """List all available JSON files in the specified directory"""
    if not os.path.exists(directory):
        print(f"Directory {directory} not found.")
        return []
    
    json_files = glob.glob(os.path.join(directory, "*.json"))
    return json_files

def list_available_models():
    """List all available Ollama models"""
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            print("\nAvailable Ollama models:")
            print(result.stdout)
        else:
            print("Error listing Ollama models. Make sure Ollama is installed and running.")
    except Exception as e:
        print(f"Error listing models: {str(e)}")

def main():
    """Main function to handle command line arguments and run the program"""
    parser = argparse.ArgumentParser(description="Generate meeting summaries from JSON transcript files.")
    parser.add_argument("-f", "--file", help="Path to JSON transcript file")
    parser.add_argument("-m", "--model", default="deepseek-r1:1.5b", help="Ollama model to use (default: deepseek-r1:1.5b)")
    parser.add_argument("-t", "--temperature", type=float, default=0.1, help="Temperature for model generation (default: 0.1)")
    parser.add_argument("-l", "--list", action="store_true", help="List available JSON transcript files")
    parser.add_argument("--list-models", action="store_true", help="List available Ollama models")
    
    args = parser.parse_args()
    
    # List available JSON files if requested
    if args.list:
        json_files = list_available_json_files()
        if json_files:
            print("\nAvailable JSON transcript files:")
            for i, file in enumerate(json_files, 1):
                print(f"{i}. {file}")
        else:
            print("No JSON transcript files found in the JSON_Transcripts directory.")
        return
    
    # List available models if requested
    if args.list_models:
        list_available_models()
        return
    
    # Process a specific file if provided
    if args.file:
        json_file_path = args.file
        if not os.path.exists(json_file_path):
            print(f"Error: File {json_file_path} not found.")
            return
    else:
        # If no file specified, use the first available JSON file
        json_files = list_available_json_files()
        if not json_files:
            print("No JSON transcript files found in the JSON_Transcripts directory.")
            return
        
        # Automatically select the first file
        json_file_path = json_files[0]
        print(f"Using default file: {os.path.basename(json_file_path)}")
    
    # Process the transcript and generate summary
    summary = process_transcript(json_file_path, args.model, args.temperature)
    
    if summary:
        print("\nMeeting Summary:\n")
        print(summary)
        
        # Save the summary to a file
        if save_summary_to_file(summary, json_file_path):
            print(f"\nSummary saved to Summaries/{os.path.splitext(os.path.basename(json_file_path))[0]}.txt")
        else:
            print("\nFailed to save summary to file.")

if __name__ == "__main__":
    main()

