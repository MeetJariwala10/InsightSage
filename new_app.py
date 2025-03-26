import streamlit as st
import os
import subprocess
import time
import json
import glob
import re
import smtplib
import ssl
from email.message import EmailMessage

# Add custom CSS for conversation boxes and animated gradient title
st.markdown("""
    <style>
    /* Animated gradient title */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
    
    .title-container {
        position: relative;
        background: linear-gradient(-45deg, rgba(238, 119, 82, 0.15), rgba(231, 60, 126, 0.15), rgba(35, 166, 213, 0.15), rgba(35, 213, 171, 0.15));
        background-size: 400% 400%;
        animation: gradient-bg 15s ease infinite;
        border-radius: 20px;
        padding: 3rem 1rem 2.5rem;
        margin: 1rem 0 3rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        overflow: hidden;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Floating particles */
    .particle {
        position: absolute;
        border-radius: 50%;
        opacity: 0.5;
        z-index: 0;
    }
    
    .particle:nth-child(1) {
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(238, 119, 82, 0.4) 0%, rgba(238, 119, 82, 0) 70%);
        top: 20%;
        left: 10%;
        animation: float1 12s ease-in-out infinite;
    }
    
    .particle:nth-child(2) {
        width: 150px;
        height: 150px;
        background: radial-gradient(circle, rgba(231, 60, 126, 0.4) 0%, rgba(231, 60, 126, 0) 70%);
        top: 60%;
        left: 80%;
        animation: float2 15s ease-in-out infinite;
    }
    
    .particle:nth-child(3) {
        width: 120px;
        height: 120px;
        background: radial-gradient(circle, rgba(35, 166, 213, 0.4) 0%, rgba(35, 166, 213, 0) 70%);
        top: 40%;
        left: 30%;
        animation: float3 18s ease-in-out infinite;
    }
    
    .particle:nth-child(4) {
        width: 80px;
        height: 80px;
        background: radial-gradient(circle, rgba(35, 213, 171, 0.4) 0%, rgba(35, 213, 171, 0) 70%);
        top: 80%;
        left: 50%;
        animation: float4 20s ease-in-out infinite;
    }
    
    @keyframes float1 {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        25% { transform: translate(-20px, 30px) rotate(10deg); }
        50% { transform: translate(20px, 20px) rotate(20deg); }
        75% { transform: translate(10px, -30px) rotate(10deg); }
    }
    
    @keyframes float2 {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        25% { transform: translate(30px, -20px) rotate(-10deg); }
        50% { transform: translate(-20px, -10px) rotate(-20deg); }
        75% { transform: translate(-30px, 30px) rotate(-10deg); }
    }
    
    @keyframes float3 {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        25% { transform: translate(-10px, -15px) rotate(5deg); }
        50% { transform: translate(15px, 10px) rotate(10deg); }
        75% { transform: translate(5px, 15px) rotate(5deg); }
    }
    
    @keyframes float4 {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        25% { transform: translate(15px, 10px) rotate(-5deg); }
        50% { transform: translate(-10px, -10px) rotate(-10deg); }
        75% { transform: translate(-15px, -5px) rotate(-5deg); }
    }
    
    /* Shimmer effect for the title */
    .title-gradient {
        font-family: 'Poppins', sans-serif;
        font-size: 4rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(-70deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 200% 200%;
        color: transparent;
        background-clip: text;
        -webkit-background-clip: text;
        animation: gradient 8s ease infinite;
        margin-bottom: 0.6rem;
        letter-spacing: -0.01em;
        position: relative;
        z-index: 2;
        text-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
    }
    
    .subtitle-text {
        font-family: 'Poppins', sans-serif;
        text-align: center;
        font-size: 1.3rem;
        opacity: 0.85;
        margin-bottom: 0.6rem;
        position: relative;
        z-index: 2;
    }
    
    .powered-by {
        font-family: 'Poppins', sans-serif;
        text-align: center;
        font-size: 1rem;
        opacity: 0.7;
        font-style: italic;
        position: relative;
        z-index: 2;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes gradient-bg {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .conversation-box-user {
       text-align: right;
       background-color: #2D3748;
       color: white;
       padding: 10px;
       border-radius: 10px;
       margin-bottom: 5px;
    }
    .conversation-box-assistant {
       text-align: left;
       background-color: #4A5568;
       color: white;
       padding: 10px;
       border-radius: 10px;
       margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Debug print to check if the file is being executed
print("Starting new_app.py - Debugging")

# Set ffmpeg path explicitly to avoid pydub warning
def get_ffmpeg_path():
    """Get the path to ffmpeg executable."""
    ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg-master-latest-win64-gpl-shared", 
                             "ffmpeg-master-latest-win64-gpl-shared", "bin")
    ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg.exe")
    
    if not os.path.exists(ffmpeg_path):
        st.error(f"ffmpeg not found at {ffmpeg_path}")
        st.error("Please ensure ffmpeg is installed in the correct location.")
        return None
    
    return ffmpeg_dir

# Add ffmpeg to PATH
ffmpeg_dir = get_ffmpeg_path()
if ffmpeg_dir:
    os.environ["PATH"] += os.pathsep + ffmpeg_dir
else:
    st.error("ffmpeg not found. Audio processing features will not be available.")
    st.stop()

# Only import what we need
try:
    from langchain.docstore.document import Document
    from langchain_ollama import OllamaLLM
    from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    from typing import List
    print("All imports successful")
except ImportError as e:
    st.error(f"Import error: {e}. This may cause the app to fail.")

# Helper function to run a subprocess (terminal outputs removed)
def run_script(script_name, audio_file_path=None):
    if not os.path.exists(script_name):
        st.error(f"Script file not found: {script_name}")
        return f"ERROR: Script file not found: {script_name}"
    
    try:
        cmd = ['python', script_name]
        if audio_file_path:
            cmd.extend(['--file', audio_file_path])
            
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        output = ""
        for line in process.stdout:
            output += line
        process.wait()
        if process.returncode != 0:
            st.error(f"Script {script_name} exited with error code {process.returncode}")
        return output
    except Exception as e:
        st.error(f"Error running script {script_name}: {str(e)}")
        return f"ERROR: {str(e)}"

# Function to remove any <think>...</think> tags and their content
def remove_think_tags(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.replace("<think>", "").replace("</think>", "")
    return text

# Function to extract tasks from the meeting summary
def extract_tasks(summary):
    tasks = {}
    
    # First, try to find the action items section with standard markdown heading
    action_items_section = re.search(r'## ACTION ITEMS\n(.*?)(\n##|$)', summary, re.DOTALL)
    
    # If not found, try alternative formats that might be in the summary
    if not action_items_section:
        action_items_section = re.search(r'Action Items:?\n(.*?)(\n#|\n\n\w|$)', summary, re.DOTALL)
    
    if not action_items_section:
        action_items_section = re.search(r'ACTION ITEMS:?\n(.*?)(\n#|\n\n\w|$)', summary, re.DOTALL)
        
    if action_items_section:
        lines = action_items_section.group(1).strip().split('\n')
        for line in lines:
            # Match multiple formats:
            # - Name: Task - Deadline
            # - [Name]: Task - Deadline
            # - Name - Task - Deadline
            # - Name: Task (Deadline)
            
            # Try the standard format first
            match = re.match(r'-\s+([^:]+):\s+(.+?)\s+-\s+(.+)', line.strip())
            
            # Try alternate formats if first pattern doesn't match
            if not match:
                match = re.match(r'-\s+\[([^\]]+)\]:\s+(.+?)\s+-\s+(.+)', line.strip())
            
            if not match:
                match = re.match(r'-\s+([^-]+)\s+-\s+(.+?)\s+-\s+(.+)', line.strip())
                
            if not match:
                match = re.match(r'-\s+([^:]+):\s+(.+?)\s+\((.+?)\)', line.strip())
                
            if match:
                name, task, deadline = match.groups()
                name = name.strip()
                participants = get_participants()
                
                # Try exact match first (case-insensitive)
                found_match = False
                for email, person in participants.items():
                    if name.lower() == person.lower():
                        tasks[email] = {'name': person, 'task': task.strip(), 'deadline': deadline.strip()}
                        found_match = True
                        break
                
                # If no exact match, try partial matches and common name variations
                if not found_match:
                    for email, person in participants.items():
                        # Check for name variations (first name, last name, or partial match)
                        person_parts = person.lower().split()
                        name_parts = name.lower().split()
                        
                        if (any(part in name.lower() for part in person_parts) or
                            any(part in person.lower() for part in name_parts) or
                            name.lower().startswith(person.lower()) or 
                            person.lower().startswith(name.lower())):
                            
                            tasks[email] = {'name': person, 'task': task.strip(), 'deadline': deadline.strip()}
                            found_match = True
                            break
    
    return tasks

# New function to extract tasks directly from transcript using LangChain Ollama agent
def extract_tasks_with_agent(json_file_path, custom_prompt="", model_name="deepseek-r1:1.5b", temperature=0.1):
    """
    Extract tasks directly from transcript data using LangChain and Ollama
    
    Args:
        json_file_path: Path to the JSON transcript file
        custom_prompt: Custom instructions for task extraction
        model_name: Name of the Ollama model to use
        temperature: Temperature setting for the model
        
    Returns:
        Dictionary of tasks with email keys and task details
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)
    except Exception as e:
        st.error(f"Error loading transcript JSON: {e}")
        return {}

    # Format the transcript data
    if isinstance(transcript_data, dict) and not isinstance(transcript_data, list):
        transcript_list = [msg_data for msg_id, msg_data in transcript_data.items()]
        transcript_list.sort(key=lambda x: x['timestamp'])
        transcript_data = transcript_list
    
    try:
        if isinstance(transcript_data, list):
            combined_text = "\n".join(
                [f"[{item.get('timestamp', '')}] {item.get('speaker', '')}: {item.get('text', item.get('message', ''))}" 
                 for item in transcript_data]
            )
        else:
            st.error("Unknown transcript format")
            return {}
    except Exception as e:
        st.error(f"Error processing transcript data: {e}")
        return {}
    
    # Get list of participants to help with task assignment
    participants = get_participants()
    participant_names_str = ", ".join(participants.values())
    
    # Default prompt if custom prompt is not provided
    if not custom_prompt:
        custom_prompt = f"""Extract all tasks, assignments, and action items from this meeting transcript.
For each task, identify:
1. The specific person assigned to the task
2. The detailed task description
3. Any deadline or due date mentioned

Format each task exactly as: "Person: Task - Deadline"
If no deadline is specified, use "Not specified" instead.

Focus only on tasks clearly assigned to someone during the meeting.
"""

    # Create system prompt
    system_template = f"""You are an AI agent specialized in identifying tasks, action items, and responsibilities from meeting transcripts.
Your job is to carefully read the transcript and extract tasks that are assigned to specific individuals.

The meeting participants are: {participant_names_str}

{custom_prompt}
"""

    human_template = """Here's the meeting transcript:
{transcript}

Extract all tasks and assignments in the specified format.
"""

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ])
    
    try:
        llm = OllamaLLM(model=model_name, temperature=temperature)
    except Exception as e:
        st.error(f"Error initializing Ollama LLM: {e}")
        return {}

    chain = ({"transcript": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    
    try:
        result = chain.invoke(combined_text)
        result = remove_think_tags(result)
        
        # Process the raw result into a structured tasks dictionary
        tasks = {}
        lines = result.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Extract task information with flexible pattern matching
            # Try different formats:
            # Person: Task - Deadline
            # - Person: Task - Deadline
            if line.startswith('-'):
                line = line[1:].strip()
                
            # Parse: "Person: Task - Deadline"
            match = re.match(r'([^:]+):\s*(.+?)\s*-\s*(.+)', line)
            if not match:
                # Try without the dash: "Person: Task (Deadline)" or similar
                match = re.match(r'([^:]+):\s*(.+?)\s*\((.+?)\)', line)
                
            if match:
                name, task, deadline = match.groups()
                name = name.strip()
                
                # Try to match the name with participants
                found_match = False
                for email, person in participants.items():
                    if name.lower() == person.lower():
                        tasks[email] = {'name': person, 'task': task.strip(), 'deadline': deadline.strip()}
                        found_match = True
                        break
                
                # If no exact match, try partial matches
                if not found_match:
                    for email, person in participants.items():
                        person_parts = person.lower().split()
                        name_parts = name.lower().split()
                        
                        if (any(part in name.lower() for part in person_parts) or
                            any(part in person.lower() for part in name_parts) or
                            name.lower().startswith(person.lower()) or 
                            person.lower().startswith(name.lower())):
                            
                            tasks[email] = {'name': person, 'task': task.strip(), 'deadline': deadline.strip()}
                            break
        
        return tasks
    except Exception as e:
        st.error(f"Error generating tasks: {str(e)}")
        return {}

# Function to generate the meeting summary using the JSON transcript
def generate_meeting_summary(json_file_path, model_name="deepseek-r1:1.5b", temperature=0.1):
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)
    except Exception as e:
        st.error(f"Error loading transcript JSON: {e}")
        return None

    if isinstance(transcript_data, dict) and not isinstance(transcript_data, list):
        transcript_list = [msg_data for msg_id, msg_data in transcript_data.items()]
        transcript_list.sort(key=lambda x: x['timestamp'])
        transcript_data = transcript_list
    
    try:
        if isinstance(transcript_data, list):
            combined_text = "\n".join(
                [f"[{item.get('timestamp', '')}] {item.get('speaker', '')}: {item.get('text', item.get('message', ''))}" 
                 for item in transcript_data]
            )
        else:
            st.error("Unknown transcript format")
            return None
    except Exception as e:
        st.error(f"Error processing transcript data: {e}")
        return None

    # First, get participant names to help with task assignment
    participants = get_participants()
    participant_names = list(participants.values())
    participant_names_str = ", ".join(participant_names)
    
    # Create system prompt
    system_template = f"""You are an AI agent specialized in analyzing meeting transcripts and generating concise summaries.
Your job is to carefully read the transcript and create a clear, well-structured summary that captures the key points.

The meeting participants are: {participant_names_str}

Focus on:
1. Main topics discussed
2. Key decisions made
3. Action items and tasks assigned
4. Important deadlines mentioned
5. Any follow-up meetings or next steps

Format the summary in a clear, readable way with appropriate sections and bullet points.
"""

    human_template = """Here's the meeting transcript:
{transcripts}

Generate a clear, well-structured summary following the specified format.
"""

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ])
    
    try:
        llm = OllamaLLM(model=model_name, temperature=temperature)
    except Exception as e:
        st.error(f"Error initializing Ollama LLM: {e}")
        return None

    chain = ({"transcripts": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    
    try:
        result = chain.invoke(combined_text)
        result = remove_think_tags(result)
        return result
    except Exception as e:
        st.error(f"Error generating meeting summary: {str(e)}")
        return None

# Function to generate a follow-up chat response using the transcript as context
def generate_chat_response(question, json_file_path, model_name="deepseek-r1:1.5b", temperature=0.1):
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)
    except Exception as e:
        st.error(f"Error loading transcript JSON: {e}")
        return "Error: Could not load transcript data."

    if isinstance(transcript_data, dict) and not isinstance(transcript_data, list):
        transcript_list = [msg_data for msg_id, msg_data in transcript_data.items()]
        transcript_list.sort(key=lambda x: x['timestamp'])
        transcript_data = transcript_list
    
    try:
        if isinstance(transcript_data, list):
            combined_text = "\n".join(
                [f"[{item.get('timestamp', '')}] {item.get('speaker', '')}: {item.get('text', item.get('message', ''))}" 
                 for item in transcript_data]
            )
        else:
            st.error("Unknown transcript format")
            return "Error: Invalid transcript format."
    except Exception as e:
        st.error(f"Error processing transcript data: {e}")
        return "Error: Could not process transcript data."

    # Get participant names for context
    participants = get_participants()
    participant_names_str = ", ".join(participants.values())
    
    # Create system prompt
    system_template = f"""You are an AI assistant helping to answer questions about a meeting transcript.
Your job is to provide accurate, relevant answers based on the transcript content.

The meeting participants are: {participant_names_str}

Guidelines:
1. Only answer based on information present in the transcript
2. If the information is not in the transcript, say so clearly
3. Be concise but thorough
4. If you're unsure about something, acknowledge the uncertainty
5. Use the participant names from the transcript when referring to people
"""

    human_template = """Here's the meeting transcript:
{transcripts}

Question: {question}

Please provide a clear, accurate answer based on the transcript content.
"""

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ])
    
    try:
        llm = OllamaLLM(model=model_name, temperature=temperature)
    except Exception as e:
        st.error(f"Error initializing Ollama LLM: {e}")
        return "Error: Could not initialize the AI model."

    chain = ({"transcripts": RunnablePassthrough(), "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    
    try:
        response = chain.invoke({"transcripts": combined_text, "question": question})
        response = remove_think_tags(response)
        return response.strip()
    except Exception as e:
        st.error(f"Error generating chat response: {str(e)}")
        return "Error: Could not generate a response."

# Function to convert MP3 to WAV using ffmpeg subprocess call (debug outputs removed)
def convert_mp3_to_wav_direct(mp3_path, wav_path):
    try:
        ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg-master-latest-win64-gpl-shared", 
                                   "ffmpeg-master-latest-win64-gpl-shared", "bin", "ffmpeg.exe")
        if not os.path.exists(ffmpeg_path):
            st.error(f"ffmpeg not found at {ffmpeg_path}")
            return False
        
        if not os.path.exists(mp3_path):
            st.error(f"Input MP3 file not found: {mp3_path}")
            return False
            
        os.makedirs(os.path.dirname(wav_path), exist_ok=True)
        cmd = [ffmpeg_path, "-y", "-i", mp3_path, "-acodec", "pcm_s16le", "-ar", "44100", wav_path]
        
        process = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if process.returncode == 0:
            if os.path.exists(wav_path):
                st.success(f"Successfully converted {mp3_path} to {wav_path}")
                return True
            else:
                st.error("ffmpeg reported success but WAV file was not created")
                return False
        else:
            st.error(f"ffmpeg conversion failed with return code {process.returncode}")
            return False
    except Exception as e:
        st.error(f"Error during conversion: {str(e)}")
        return False

# Function to validate an MP3 file
def validate_mp3(file_path):
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
        is_id3 = header[:3] == b'ID3'
        is_mpeg = header[0] == 0xFF and (header[1] & 0xE0) == 0xE0
        if is_id3 or is_mpeg:
            return True, "Valid MP3 file"
        else:
            return False, f"Invalid MP3 header: {header.hex()}"
    except Exception as e:
        return False, f"Error validating MP3: {str(e)}"

# Function to get participant emails
def get_participants():
    if "participants" not in st.session_state:
        # Default participants
        st.session_state.participants = {
            'mananparekh.co22d2@scet.ac.in': 'Manan',
            'meetjariwala.co22d1@scet.ac.in': 'Meet',
            'dhruvilpatel.co22d2@scet.ac.in': 'Dhruvil',
            'mokshagrawal.co22d1@scet.ac.in': 'Moksh'
        }
    return st.session_state.participants

# Function to update a participant
def update_participant(email, name):
    participants = get_participants()
    participants[email] = name
    st.session_state.participants = participants

# Function to remove a participant
def remove_participant(email):
    participants = get_participants()
    if email in participants:
        del participants[email]
        st.session_state.participants = participants

# Function to send email
def send_email(receiver_email, subject, body, sender_email=None, sender_password=None):
    try:
        if not sender_email:
            sender_email = st.session_state.get('email_sender', '')
        if not sender_password:
            sender_password = st.session_state.get('email_password', '')
        
        if not sender_email or not sender_password:
            st.error("Email sender and password are required")
            return False
            
        em = EmailMessage()
        em['From'] = sender_email
        em['To'] = receiver_email
        em['Subject'] = subject
        em.set_content(body)
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(em)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

# Main Streamlit app interface - replace the regular title with our animated gradient title
st.markdown("""
<div class="title-container">
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <h1 class="title-gradient">InsightSage</h1>
    <p class="subtitle-text">Dynamic Meeting Transcript Processor & Interactive Chatbot</p>
    <p class="powered-by">Powered by AI</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
This application allows you to upload an MP3 file which will be processed into a transcript, summary, and an interactive chatbot interface.  
You can also use the file browser, diagnostics, and other utilities from the sidebar.
""")

for d in ["Audio", "WAV_Audio", "TEXT_Transcripts", "JSON_Transcripts", "Summaries"]:
    os.makedirs(d, exist_ok=True)

auto_process = st.checkbox("Automatically process upon upload", value=True)
use_ai_agent = st.checkbox("Use AI agent for task extraction (with custom prompt)", value=False)
show_debug = st.sidebar.checkbox("Debug Mode", value=False)
uploaded_file = st.file_uploader("Upload an MP3 file", type=["mp3"])

# Show custom prompt input if AI agent option is selected
custom_task_prompt = ""
if use_ai_agent:
    custom_task_prompt = st.text_area(
        "Custom task extraction instructions:",
        height=100,
        placeholder="Example: Extract all tasks mentioned in the meeting, particularly focusing on urgent items due within the next week...",
        help="Leave empty to use the default task extraction prompt"
    )

# Add email settings to the sidebar
st.sidebar.markdown("## Email Settings")
if "email_sender" not in st.session_state:
    st.session_state.email_sender = ""
if "email_password" not in st.session_state:
    st.session_state.email_password = ""
if "email_template" not in st.session_state:
    st.session_state.email_template = """Dear {name},

I hope this email finds you well. As part of our ongoing initiatives, you have been assigned the following task:

Task: {task}
Deadline: {deadline}

Please ensure that the task is completed by the given deadline. If you require any clarification or support, do not hesitate to reach out.

Your contribution to this project is highly valued, and we appreciate your dedication and effort.

Best Regards,
{coordinator}
"""

with st.sidebar.expander("Email Configuration"):
    st.text_input("Email Sender", key="email_sender", help="Your Gmail address")
    st.text_input("Email Password", key="email_password", type="password", help="Your Gmail app password")
    
    # Test email feature
    if st.button("Test Email Configuration"):
        if not st.session_state.email_sender or not st.session_state.email_password:
            st.error("Please enter your email credentials first")
        else:
            test_email = st.text_input("Send test email to:", 
                                      placeholder="recipient@example.com")
            if test_email and st.button("Send Test Email"):
                with st.spinner("Sending test email..."):
                    test_subject = "Test Email from InsightSage"
                    test_body = "This is a test email to verify your email configuration is working correctly."
                    if send_email(test_email, test_subject, test_body):
                        st.success(f"Test email sent successfully to {test_email}")
                    else:
                        st.error("Failed to send test email. Please check your credentials.")
    
    st.markdown("### Custom Email Template")
    st.text_area(
        "Email Template", 
        key="email_template", 
        height=250, 
        help="Use {name}, {task}, {deadline}, and {coordinator} as placeholders"
    )
    
    # Add a default set button
    if st.button("Reset to Default Template"):
        st.session_state.email_template = """Dear {name},

I hope this email finds you well. As part of our ongoing initiatives, you have been assigned the following task:

Task: {task}
Deadline: {deadline}

Please ensure that the task is completed by the given deadline. If you require any clarification or support, do not hesitate to reach out.

Your contribution to this project is highly valued, and we appreciate your dedication and effort.

Best Regards,
{coordinator}
"""

# Function to format email body using template and task details
def format_email_body(template, name, task, deadline, coordinator):
    return template.format(
        name=name,
        task=task,
        deadline=deadline,
        coordinator=coordinator
    )

# Add participant management to sidebar
st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.markdown("<h2>👥 Manage Participants</h2>", unsafe_allow_html=True)
with st.sidebar.expander("Manage Participants"):
    st.markdown("### Current Participants")
    participants = get_participants()
    for email, name in participants.items():
        st.text(f"{name}: {email}")
    
    st.markdown("### Add/Edit Participant")
    
    # Define a callback function for form submission
    def handle_participant_submit():
        name = st.session_state.new_participant_name
        email = st.session_state.new_participant_email
        if name and email:
            update_participant(email, name)
            st.success(f"Added/Updated {name} with email {email}")
            # We don't directly modify session state here anymore
        else:
            st.error("Both name and email are required")
    
    new_name = st.text_input("Name", key="new_participant_name")
    new_email = st.text_input("Email", key="new_participant_email")
    if st.button("Add/Update Participant", on_click=handle_participant_submit):
        pass  # The callback function will be called when the button is clicked
    
    remove_email = st.selectbox(
        "Select participant to remove",
        options=[""] + list(participants.keys()),
        format_func=lambda x: f"{participants.get(x, '')} ({x})" if x else "Select participant"
    )
    if remove_email and st.button("Remove Participant"):
        remove_participant(remove_email)
        st.success(f"Removed participant with email {remove_email}")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

if uploaded_file is not None:
    try:
        audio_file_path = os.path.join("Audio", uploaded_file.name)
        with open(audio_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Uploaded file saved as {audio_file_path}")
        
        is_valid, message = validate_mp3(audio_file_path)
        if not is_valid:
            st.error(f"Invalid MP3 file: {message}")
            if show_debug:
                st.code(f"Path: {audio_file_path}\nSize: {os.path.getsize(audio_file_path)} bytes")
        else:
            st.info(f"Valid MP3 file detected: {message}")
    except Exception as e:
        st.error(f"Error saving uploaded file: {str(e)}")
        
    if auto_process:
        st.header("Step 1: Converting MP3 to WAV")
        with st.spinner("Converting..."):
            base_filename = os.path.splitext(os.path.basename(audio_file_path))[0]
            wav_file_path = os.path.join("WAV_Audio", f"{base_filename}.wav")
            conversion_success = convert_mp3_to_wav_direct(audio_file_path, wav_file_path)
            if conversion_success:
                st.success(f"MP3 conversion completed. WAV file saved to: {wav_file_path}")
            else:
                st.error("MP3 conversion failed. Cannot proceed with transcription.")
                st.stop()
        time.sleep(1)

        st.header("Step 2: Transcribing Audio")
        with st.spinner("Transcribing audio..."):
            transcription_output = run_script("audio_transcription.py", audio_file_path)
            st.success("Audio transcription completed.")
        time.sleep(1)

        st.header("Step 3: Processing Transcript")
        with st.spinner("Processing transcript..."):
            process_output = run_script("process_transcripts.py", audio_file_path)
            st.success("Transcript processing completed.")
        time.sleep(1)

        base_filename = os.path.splitext(os.path.basename(audio_file_path))[0]
        json_transcript_path = os.path.join("JSON_Transcripts", f"{base_filename}_transcript.json")
        
        if not os.path.exists(json_transcript_path):
            st.error("JSON transcript not found. Please check the transcription step.")
        else:
            st.header("Step 4: Generating Meeting Summary")
            summary = generate_meeting_summary(json_transcript_path)
            if summary:
                st.markdown(summary)
                st.download_button(
                    label="Download Summary as Text",
                    data=summary,
                    file_name=f"{base_filename}_summary.txt",
                    mime="text/plain"
                )
                
                # Add Email functionality
                if use_ai_agent:
                    st.subheader("Extracting Tasks with AI Agent")
                    with st.spinner("Using AI agent to extract tasks from transcript..."):
                        tasks = extract_tasks_with_agent(
                            json_transcript_path,
                            custom_prompt=custom_task_prompt,
                            model_name="deepseek-r1:1.5b",
                            temperature=0.1
                        )
                else:
                    # Use the traditional extraction method
                    tasks = extract_tasks(summary)
                
                if tasks:
                    st.subheader("Email Task Assignments")
                    st.write("The following tasks were identified and can be emailed to participants:")
                    
                    for email, details in tasks.items():
                        st.write(f"- {details['name']}: {details['task']} (Due: {details['deadline']})")
                    
                    coordinator_name = st.text_input("Coordinator Name", value="Team Coordinator")
                    
                    if st.button("Send Task Emails"):
                        if not st.session_state.email_sender or not st.session_state.email_password:
                            st.error("Please enter your email credentials in the sidebar first.")
                        else:
                            with st.spinner("Sending emails..."):
                                success_count = 0
                                for email, details in tasks.items():
                                    subject = f"Task Assignment: {details['task']}"
                                    body = format_email_body(st.session_state.email_template, details['name'], details['task'], details['deadline'], coordinator_name)
                                    if send_email(email, subject, body):
                                        success_count += 1
                                
                                if success_count == len(tasks):
                                    st.success(f"Successfully sent emails to all {success_count} participants.")
                                else:
                                    st.warning(f"Sent emails to {success_count} out of {len(tasks)} participants.")
            else:
                st.error("Failed to generate meeting summary.")
            
            st.header("Chat about the Meeting")
            st.markdown("Ask follow-up questions about the meeting transcript. The transcript acts as the context for your queries.")
            
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            with st.container():
                user_question = st.text_input("Type your question here...", key="user_input")
                if st.button("Send"):
                    if user_question:
                        st.session_state.chat_history.append({"role": "user", "message": user_question})
                        with st.spinner("Generating response..."):
                            answer = generate_chat_response(user_question, json_transcript_path)
                        st.session_state.chat_history.append({"role": "assistant", "message": answer})
            
            if st.button("Reset Chat History"):
                st.session_state.chat_history = []
                st.success("Chat history reset.")
            
            st.markdown("### Conversation")
            for chat in st.session_state.chat_history:
                if chat["role"] == "user":
                    st.markdown(f"""<div class="conversation-box-user">
<strong>You:</strong> {chat['message']}
</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="conversation-box-assistant">
<strong>Assistant:</strong> {chat['message']}
</div>""", unsafe_allow_html=True)
    else:
        if st.button("1. Convert MP3 to WAV"):
            with st.spinner("Converting..."):
                base_filename = os.path.splitext(os.path.basename(audio_file_path))[0]
                wav_file_path = os.path.join("WAV_Audio", f"{base_filename}.wav")
                conversion_success = convert_mp3_to_wav_direct(audio_file_path, wav_file_path)
                if conversion_success:
                    st.success(f"MP3 conversion completed. WAV file saved to: {wav_file_path}")
                else:
                    st.error("MP3 conversion failed. Cannot proceed with transcription.")
        if st.button("2. Transcribe Audio"):
            with st.spinner("Transcribing audio..."):
                transcription_output = run_script("audio_transcription.py", audio_file_path)
                st.success("Audio transcription completed.")
        if st.button("3. Process Transcript"):
            with st.spinner("Processing transcript..."):
                process_output = run_script("process_transcripts.py", audio_file_path)
                st.success("Transcript processing completed.")

# New Transcript Viewer Section
st.markdown("## View Transcripts")
with st.expander("View Transcript Files (.txt / .json)"):
    view_option = st.selectbox("Select file type", ["txt", "json"])
    if view_option == "txt":
        txt_files = glob.glob("TEXT_Transcripts/*.txt")
        if txt_files:
            selected_txt = st.selectbox("Select a TXT transcript", [os.path.basename(f) for f in txt_files])
            if st.button("View TXT Transcript"):
                file_path = os.path.join("TEXT_Transcripts", selected_txt)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                st.text_area("Transcript (TXT)", content, height=400)
        else:
            st.info("No TXT transcript files found.")
    else:
        json_files = glob.glob("JSON_Transcripts/*.json")
        if json_files:
            selected_json = st.selectbox("Select a JSON transcript", [os.path.basename(f) for f in json_files])
            if st.button("View JSON Transcript"):
                file_path = os.path.join("JSON_Transcripts", selected_json)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                st.json(content)
        else:
            st.info("No JSON transcript files found.")

# Add custom task extraction agent section
st.markdown("## Custom Task Extraction Agent")
with st.expander("Extract tasks directly from transcript with custom instructions"):
    st.markdown("""
    This tool allows you to extract tasks and assignments directly from meeting transcripts using 
    a custom prompt to guide the AI agent. You can specify exactly what to look for and how to interpret
    the transcript.
    """)
    
    json_files = glob.glob("JSON_Transcripts/*.json")
    if json_files:
        agent_transcript = st.selectbox(
            "Select transcript for task extraction:", 
            [os.path.basename(f) for f in json_files],
            key="agent_transcript"
        )
        
        custom_prompt = st.text_area(
            "Custom extraction instructions (optional):", 
            height=150,
            placeholder="Example: Extract all tasks mentioned in the meeting, particularly focusing on urgent items due within the next week...",
            help="Leave empty to use the default task extraction prompt"
        )
        
        model_col, temp_col = st.columns(2)
        with model_col:
            agent_model = st.selectbox(
                "Select Ollama model:",
                ["deepseek-r1:1.5b", "llama3", "mistral", "gemma:2b"],
                index=0,
                key="agent_model"
            )
        
        with temp_col:
            agent_temp = st.slider(
                "Temperature:",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.1,
                key="agent_temp"
            )
        
        if st.button("Extract Tasks with Agent"):
            with st.spinner("Analyzing transcript with AI agent..."):
                json_path = os.path.join("JSON_Transcripts", agent_transcript)
                tasks = extract_tasks_with_agent(
                    json_path,
                    custom_prompt=custom_prompt,
                    model_name=agent_model,
                    temperature=agent_temp
                )
                
                if tasks:
                    st.success(f"Found {len(tasks)} tasks in the transcript")
                    
                    st.subheader("Extracted Tasks")
                    for email, details in tasks.items():
                        st.markdown(f"""
                        **Person:** {details['name']} ({email})  
                        **Task:** {details['task']}  
                        **Deadline:** {details['deadline']}
                        ---
                        """)
                    
                    # Add option to email these tasks
                    if st.button("Email These Tasks"):
                        if not st.session_state.email_sender or not st.session_state.email_password:
                            st.error("Please enter your email credentials in the sidebar first.")
                        else:
                            coordinator_name = st.text_input("Coordinator Name", value="Team Coordinator")
                            with st.spinner("Sending emails..."):
                                success_count = 0
                                for email, details in tasks.items():
                                    subject = f"Task Assignment: {details['task']}"
                                    body = format_email_body(
                                        st.session_state.email_template, 
                                        details['name'], 
                                        details['task'], 
                                        details['deadline'], 
                                        coordinator_name
                                    )
                                    if send_email(email, subject, body):
                                        success_count += 1
                                
                                if success_count == len(tasks):
                                    st.success(f"Successfully sent emails to all {success_count} participants.")
                                else:
                                    st.warning(f"Sent emails to {success_count} out of {len(tasks)} participants.")
                else:
                    st.info("No tasks were found in the transcript.")
    else:
        st.info("No JSON transcript files available. Please upload and process a meeting audio file first.")

# Sidebar: Diagnostics, File Browser, and More
st.sidebar.markdown("## Diagnostics")
if st.sidebar.button("Test Ollama Connection"):
    try:
        from langchain_ollama import OllamaLLM
        st.sidebar.info("Testing connection to Ollama with deepseek-r1:1.5b...")
        llm = OllamaLLM(model="deepseek-r1:1.5b", temperature=0.1)
        response = llm.invoke("Say hello in one word")
        st.sidebar.success(f"Ollama test successful! Response: {response}")
    except Exception as e:
        st.sidebar.error(f"Ollama connection failed: {str(e)}")
        st.sidebar.markdown("""
        ### Possible issues:
        1. Ollama is not running - start it with `ollama serve`
        2. Ollama doesn't have the required model - run `ollama pull deepseek-r1:1.5b`
        3. Network or firewall issues
        """)
        
if st.sidebar.button("Check Files"):
    st.sidebar.markdown("## Directory Check")
    for d in ["Audio", "WAV_Audio", "TEXT_Transcripts", "JSON_Transcripts", "Summaries"]:
        if os.path.exists(d):
            st.sidebar.success(f"✅ {d} directory exists")
        else:
            st.sidebar.error(f"❌ {d} directory missing")
            
    st.sidebar.markdown("## Audio Files")
    audio_files = glob.glob("Audio/*.mp3")
    wav_files = glob.glob("WAV_Audio/*.wav")
    if audio_files:
        st.sidebar.success(f"✅ Found {len(audio_files)} MP3 files")
        for file in audio_files:
            st.sidebar.info(f"- {os.path.basename(file)}")
    else:
        st.sidebar.warning("⚠️ No MP3 files found")
    if wav_files:
        st.sidebar.success(f"✅ Found {len(wav_files)} WAV files")
        for file in wav_files:
            st.sidebar.info(f"- {os.path.basename(file)}")
    else:
        st.sidebar.warning("⚠️ No WAV files found")
        
    st.sidebar.markdown("## Transcript Files")
    text_files = glob.glob("TEXT_Transcripts/*_transcript.txt")
    json_files = glob.glob("JSON_Transcripts/*_transcript.json")
    if text_files:
        st.sidebar.success(f"✅ Found {len(text_files)} transcript text files")
        for file in text_files:
            st.sidebar.info(f"- {os.path.basename(file)}")
    else:
        st.sidebar.warning("⚠️ No transcript text files found")
    if json_files:
        st.sidebar.success(f"✅ Found {len(json_files)} transcript JSON files")
        for file in json_files:
            st.sidebar.info(f"- {os.path.basename(file)}")
    else:
        st.sidebar.warning("⚠️ No transcript JSON files found")

st.sidebar.markdown("## Quick Access")
json_files = glob.glob("JSON_Transcripts/*.json")
if json_files:
    selected_json = st.sidebar.selectbox(
        "Select existing transcript for analysis:",
        options=[os.path.basename(f) for f in json_files],
        key="existing_json"
    )
    if st.sidebar.button("Generate Summary from Selected"):
        json_path = os.path.join("JSON_Transcripts", selected_json)
        with st.spinner("Generating summary from existing transcript..."):
            summary = generate_meeting_summary(json_path)
            if summary:
                st.markdown(summary)
                
                # Add Email functionality
                if use_ai_agent:
                    st.subheader("Extracting Tasks with AI Agent")
                    with st.spinner("Using AI agent to extract tasks from transcript..."):
                        tasks = extract_tasks_with_agent(
                            json_path,
                            custom_prompt=custom_task_prompt,
                            model_name="deepseek-r1:1.5b",
                            temperature=0.1
                        )
                else:
                    # Use the traditional extraction method
                    tasks = extract_tasks(summary)
                
                if tasks:
                    st.subheader("Email Task Assignments")
                    st.write("The following tasks were identified and can be emailed to participants:")
                    
                    for email, details in tasks.items():
                        st.write(f"- {details['name']}: {details['task']} (Due: {details['deadline']})")
                    
                    coordinator_name = st.text_input("Coordinator Name", value="Team Coordinator")
                    
                    if st.button("Send Task Emails"):
                        if not st.session_state.email_sender or not st.session_state.email_password:
                            st.error("Please enter your email credentials in the sidebar first.")
                        else:
                            with st.spinner("Sending emails..."):
                                success_count = 0
                                for email, details in tasks.items():
                                    subject = f"Task Assignment: {details['task']}"
                                    body = format_email_body(st.session_state.email_template, details['name'], details['task'], details['deadline'], coordinator_name)
                                    if send_email(email, subject, body):
                                        success_count += 1
                                
                                if success_count == len(tasks):
                                    st.success(f"Successfully sent emails to all {success_count} participants.")
                                else:
                                    st.warning(f"Sent emails to {success_count} out of {len(tasks)} participants.")
                else:
                    st.info("No tasks were found in the summary that could be assigned to participants.")
            else:
                st.error("Failed to generate meeting summary.")
    else:
        st.sidebar.info("No JSON transcripts available for quick analysis")

st.sidebar.markdown("## Script Tests")
if st.sidebar.button("Test MP3 to WAV Conversion"):
    audio_files = glob.glob("Audio/*.mp3")
    if audio_files:
        test_file = audio_files[0]
        st.sidebar.info(f"Testing with {os.path.basename(test_file)}")
        ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg-master-latest-win64-gpl-shared", 
                                  "ffmpeg-master-latest-win64-gpl-shared", "bin", "ffmpeg.exe")
        if os.path.exists(ffmpeg_path):
            st.sidebar.success(f"✅ ffmpeg.exe found at: {ffmpeg_path}")
            base_filename = os.path.splitext(os.path.basename(test_file))[0]
            output_wav = os.path.join("WAV_Audio", f"{base_filename}.wav")
            try:
                st.sidebar.info(f"Converting {os.path.basename(test_file)} to {os.path.basename(output_wav)}...")
                result = convert_mp3_to_wav_direct(test_file, output_wav)
                if result:
                    st.sidebar.success("✅ Direct ffmpeg conversion successful!")
                    st.sidebar.info(f"Output file: {output_wav}")
                else:
                    st.sidebar.error("❌ Direct ffmpeg conversion failed!")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")
        else:
            st.sidebar.error(f"❌ ffmpeg.exe NOT found at: {ffmpeg_path}")
    else:
        st.sidebar.warning("⚠️ No MP3 files found for testing")

st.sidebar.markdown("## File Selection")
existing_audio_files = glob.glob("Audio/*.mp3")
if existing_audio_files:
    audio_options = [os.path.basename(f) for f in existing_audio_files]
    selected_audio = st.sidebar.selectbox(
        "Select existing MP3 file:",
        options=["None"] + audio_options
    )
    if selected_audio != "None":
        if st.sidebar.button("Use Selected File"):
            audio_file_path = os.path.join("Audio", selected_audio)
            st.info(f"Using selected file: {audio_file_path}")
            is_valid, message = validate_mp3(audio_file_path)
            if not is_valid:
                st.error(f"Invalid MP3 file: {message}")
                if show_debug:
                    st.code(f"Path: {audio_file_path}\nSize: {os.path.getsize(audio_file_path)} bytes")
            else:
                st.header("Step 1: Converting MP3 to WAV")
                with st.spinner("Converting..."):
                    base_filename = os.path.splitext(os.path.basename(audio_file_path))[0]
                    wav_file_path = os.path.join("WAV_Audio", f"{base_filename}.wav")
                    conversion_success = convert_mp3_to_wav_direct(audio_file_path, wav_file_path)
                    if conversion_success:
                        st.success(f"MP3 conversion completed. WAV file saved to: {wav_file_path}")
                        st.header("Step 2: Transcribing Audio")
                        with st.spinner("Transcribing audio..."):
                            transcription_output = run_script("audio_transcription.py", audio_file_path)
                            st.success("Audio transcription completed.")
                        st.header("Step 3: Processing Transcript")
                        with st.spinner("Processing transcript..."):
                            process_output = run_script("process_transcripts.py", audio_file_path)
                            st.success("Transcript processing completed.")
                        json_transcript_path = os.path.join("JSON_Transcripts", f"{base_filename}_transcript.json")
                        if os.path.exists(json_transcript_path):
                            st.header("Step 4: Generating Meeting Summary")
                            summary = generate_meeting_summary(json_transcript_path)
                            if summary:
                                st.markdown(summary)
                                st.download_button(
                                    label="Download Summary as Text",
                                    data=summary,
                                    file_name=f"{base_filename}_summary.txt",
                                    mime="text/plain"
                                )
                                
                                # Add Email functionality
                                if use_ai_agent:
                                    st.subheader("Extracting Tasks with AI Agent")
                                    with st.spinner("Using AI agent to extract tasks from transcript..."):
                                        tasks = extract_tasks_with_agent(
                                            json_transcript_path,
                                            custom_prompt=custom_task_prompt,
                                            model_name="deepseek-r1:1.5b",
                                            temperature=0.1
                                        )
                                else:
                                    # Use the traditional extraction method
                                    tasks = extract_tasks(summary)
                                
                                if tasks:
                                    st.subheader("Email Task Assignments")
                                    st.write("The following tasks were identified and can be emailed to participants:")
                                    
                                    for email, details in tasks.items():
                                        st.write(f"- {details['name']}: {details['task']} (Due: {details['deadline']})")
                                    
                                    coordinator_name = st.text_input("Coordinator Name", value="Team Coordinator")
                                    
                                    if st.button("Send Task Emails"):
                                        if not st.session_state.email_sender or not st.session_state.email_password:
                                            st.error("Please enter your email credentials in the sidebar first.")
                                        else:
                                            with st.spinner("Sending emails..."):
                                                success_count = 0
                                                for email, details in tasks.items():
                                                    subject = f"Task Assignment: {details['task']}"
                                                    body = format_email_body(st.session_state.email_template, details['name'], details['task'], details['deadline'], coordinator_name)
                                                    if send_email(email, subject, body):
                                                        success_count += 1
                                                
                                                if success_count == len(tasks):
                                                    st.success(f"Successfully sent emails to all {success_count} participants.")
                                                else:
                                                    st.warning(f"Sent emails to {success_count} out of {len(tasks)} participants.")
                            else:
                                st.error("Failed to generate meeting summary.")
                        else:
                            st.error(f"JSON transcript not found at: {json_transcript_path}")
                    else:
                        st.error("MP3 conversion failed. Cannot proceed with transcription.")
else:
    st.sidebar.info("No MP3 files found in the Audio directory")


