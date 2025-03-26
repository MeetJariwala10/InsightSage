import streamlit as st
import os
import sys
import glob
import json
import torch
import numpy as np
from datetime import datetime
import subprocess
import tempfile
from sentence_transformers import SentenceTransformer

# Import functions from existing scripts
sys.path.append(os.getcwd())
try:
    from mp3_to_wav import convert_mp3_to_wav
    from audio_transcription import load_audio, format_timestamp
    from process_transcripts import process_transcript_file, save_to_json
    from transcripts_ollama import process_transcript as generate_summary
    from transcripts_vdb import search_transcripts, model
except ImportError as e:
    st.error(f"Error importing modules: {e}")

st.set_page_config(
    page_title="MindHybrid Meeting Analyzer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for navigation
st.sidebar.title("MindHybrid Meeting Analyzer")
app_mode = st.sidebar.selectbox(
    "Choose a mode",
    ["Home", "Convert Audio", "Transcribe Audio", "Process Transcripts", "Search Transcripts", "Generate Summaries"]
)

# Home page
if app_mode == "Home":
    st.title("🎙️ MindHybrid Meeting Analyzer")
    st.subheader("Analyze and extract insights from your meeting recordings")
    
    st.markdown("""
    ### Features:
    - **Convert Audio**: Convert MP3 files to WAV format for processing
    - **Transcribe Audio**: Automatically transcribe audio files with speaker diarization
    - **Process Transcripts**: Structure and organize your transcripts
    - **Search Transcripts**: Semantic search through your meeting transcripts
    - **Generate Summaries**: Get AI-powered meeting summaries with key points
    
    ### How to use:
    1. Start by converting your audio to WAV format if needed
    2. Transcribe your audio files
    3. Process and organize your transcripts
    4. Search through transcripts or generate summaries
    """)
    
    # Display existing transcripts
    st.subheader("Available Transcripts")
    transcript_files = glob.glob("TEXT_Transcripts/*_transcript.txt")
    if transcript_files:
        for file in transcript_files:
            base_name = os.path.basename(file).replace("_transcript.txt", "")
            st.write(f"- {base_name}")
    else:
        st.info("No transcripts available yet. Start by converting and transcribing your audio files.")

# Convert Audio page
elif app_mode == "Convert Audio":
    st.title("Convert Audio Files")
    st.write("Convert MP3 audio files to WAV format for transcription")
    
    uploaded_file = st.file_uploader("Upload MP3 file", type=["mp3"])
    
    if uploaded_file is not None:
        # Create temp directory if it doesn't exist
        os.makedirs("Audio", exist_ok=True)
        os.makedirs("WAV_Audio", exist_ok=True)
        
        # Save uploaded file to temp directory
        mp3_path = os.path.join("Audio", uploaded_file.name)
        with open(mp3_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File uploaded: {uploaded_file.name}")
        
        # Get output filename
        wav_filename = os.path.splitext(uploaded_file.name)[0] + ".wav"
        wav_path = os.path.join("WAV_Audio", wav_filename)
        
        # Convert button
        if st.button("Convert to WAV"):
            with st.spinner("Converting audio..."):
                try:
                    # Path to ffmpeg executable
                    ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg-master-latest-win64-gpl-shared", 
                                             "ffmpeg-master-latest-win64-gpl-shared", "bin")
                    ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg.exe")
                    
                    if not os.path.exists(ffmpeg_path):
                        st.error(f"ffmpeg not found at {ffmpeg_path}. Please check installation.")
                    else:
                        convert_mp3_to_wav(mp3_path, wav_path)
                        st.success(f"Conversion complete! WAV file saved to: {wav_path}")
                except Exception as e:
                    st.error(f"Error during conversion: {str(e)}")

# Transcribe Audio page
elif app_mode == "Transcribe Audio":
    st.title("Transcribe Audio Files")
    st.write("Transcribe WAV audio files with speaker diarization")
    
    # Check for Hugging Face token
    hf_token = st.text_input("Enter your Hugging Face token:", type="password")
    
    # List available WAV files
    wav_files = glob.glob("WAV_Audio/*.wav")
    selected_file = None
    
    if wav_files:
        selected_file = st.selectbox("Select WAV file to transcribe:", 
                                    [os.path.basename(f) for f in wav_files])
    else:
        st.info("No WAV files found. Please convert audio files first.")
    
    whisper_model = st.selectbox("Select Whisper model:", 
                               ["tiny", "base", "small", "medium", "large"])
    
    if selected_file and hf_token and st.button("Transcribe Audio"):
        audio_path = os.path.join("WAV_Audio", selected_file)
        
        with st.spinner("Transcribing audio... This may take a while depending on the file size."):
            try:
                st.info("This would normally call the audio_transcription.py script.")
                st.info(f"Parameters: File={audio_path}, Model={whisper_model}, HF Token={'*' * 5}")
                
                # In a real implementation, we would call the appropriate functions 
                # from audio_transcription.py here with the selected parameters
                
                base_filename = os.path.splitext(selected_file)[0]
                txt_output_file = os.path.join("TEXT_Transcripts", f"{base_filename}_transcript.txt")
                json_output_file = os.path.join("JSON_Transcripts", f"{base_filename}_transcript.json")
                
                # For now, we'll just show a message for demonstration
                st.success(f"Transcription would be complete! Output would be saved to:")
                st.code(f"- Text file: {txt_output_file}")
                st.code(f"- JSON file: {json_output_file}")
            except Exception as e:
                st.error(f"Error during transcription: {str(e)}")

# Process Transcripts page
elif app_mode == "Process Transcripts":
    st.title("Process Transcripts")
    st.write("Process and organize transcript files")
    
    # List available transcript files
    transcript_files = glob.glob("TEXT_Transcripts/*_transcript.txt")
    
    if transcript_files:
        selected_files = st.multiselect(
            "Select transcript files to process:",
            [os.path.basename(f) for f in transcript_files]
        )
        
        if selected_files and st.button("Process Selected Transcripts"):
            with st.spinner("Processing transcripts..."):
                for filename in selected_files:
                    file_path = os.path.join("TEXT_Transcripts", filename)
                    try:
                        transcript_data, base_filename = process_transcript_file(file_path)
                        
                        if transcript_data:
                            st.write(f"Processed {len(transcript_data)} segments from {base_filename}")
                            
                            # Save the data to JSON
                            filepath = "JSON_Transcripts"
                            json_path = save_to_json(transcript_data, filepath, base_filename)
                            st.success(f"Data saved to {json_path}")
                        else:
                            st.warning(f"No valid transcript data found in {file_path}")
                    except Exception as e:
                        st.error(f"Error processing {filename}: {str(e)}")
                
                st.success("All selected transcripts processed!")
    else:
        st.info("No transcript files found. Please transcribe audio files first.")

# Search Transcripts page
elif app_mode == "Search Transcripts":
    st.title("Search Transcripts")
    st.write("Semantic search through your meeting transcripts")
    
    search_query = st.text_input("Enter your search query:")
    top_k = st.slider("Number of results to show:", min_value=1, max_value=10, value=3)
    
    if search_query and st.button("Search"):
        with st.spinner("Searching transcripts..."):
            try:
                # This would normally use the Pinecone search
                st.info("This would typically use the search_transcripts function from transcripts_vdb.py")
                st.info(f"Parameters: Query='{search_query}', Top_k={top_k}")
                
                # For now, show sample results
                st.subheader("Sample Results:")
                
                # Get all JSON transcript files
                json_files = glob.glob("JSON_Transcripts/*.json")
                
                if json_files:
                    # Load a sample file
                    with open(json_files[0], 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Show some sample results (in a real app, this would be from Pinecone)
                    st.markdown("#### Result 1")
                    st.markdown(f"**Score:** 0.87")
                    st.markdown(f"**Speaker:** {data[0]['speaker'] if 'speaker' in data[0] else 'Unknown'}")
                    st.markdown(f"**Message:** {data[0]['text'] if 'text' in data[0] else data[0].get('message', 'No text found')}")
                    
                    if len(data) > 1:
                        st.markdown("#### Result 2")
                        st.markdown(f"**Score:** 0.81")
                        st.markdown(f"**Speaker:** {data[1]['speaker'] if 'speaker' in data[1] else 'Unknown'}")
                        st.markdown(f"**Message:** {data[1]['text'] if 'text' in data[1] else data[1].get('message', 'No text found')}")
                else:
                    st.warning("No transcript data found to search through.")
            except Exception as e:
                st.error(f"Error during search: {str(e)}")

# Generate Summaries page
elif app_mode == "Generate Summaries":
    st.title("Generate Meeting Summaries")
    st.write("Generate AI-powered summaries of your meetings")
    
    # List available JSON transcript files
    json_files = glob.glob("JSON_Transcripts/*.json")
    
    if json_files:
        selected_file = st.selectbox(
            "Select transcript to summarize:",
            [os.path.basename(f) for f in json_files]
        )
        
        ollama_model = st.selectbox(
            "Select Ollama model to use:",
            ["llama3", "deepseek-r1:1.5b", "mistral", "gemma:2b"]
        )
        
        temperature = st.slider("Temperature:", min_value=0.0, max_value=1.0, value=0.1, step=0.1)
        
        if selected_file and st.button("Generate Summary"):
            file_path = os.path.join("JSON_Transcripts", selected_file)
            
            with st.spinner("Generating summary... This may take a while."):
                st.info("This would normally call the process_transcript function from transcripts_ollama.py")
                st.info(f"Parameters: File={file_path}, Model={ollama_model}, Temperature={temperature}")
                
                # In a real implementation, we would call:
                # summary = generate_summary(file_path, model_name=ollama_model, temperature=temperature)
                
                # For now, show a sample summary
                st.subheader("Sample Meeting Summary")
                st.markdown("""
                ## MEETING OVERVIEW
                Weekly sprint planning meeting to discuss project milestones and assign tasks for the upcoming sprint.
                
                ## KEY PARTICIPANTS
                - John Smith (Product Manager)
                - Sarah Johnson (Tech Lead)
                - Michael Brown (Developer)
                - Emily Davis (Designer)
                
                ## MAIN TOPICS DISCUSSED
                1. Progress on the current sprint tasks
                2. Blockers and challenges faced by the team
                3. Feature prioritization for the next release
                4. Customer feedback on recent features
                
                ## KEY DECISIONS
                1. Postpone the analytics dashboard to the next sprint
                2. Prioritize bug fixes for the payment processing system
                3. Schedule a separate UX review session for the new user interface
                
                ## ACTION ITEMS
                - Sarah: Update the API documentation by Friday
                - Michael: Fix payment processing bugs by Wednesday
                - Emily: Complete UI mockups for the new features by Thursday
                - John: Share customer feedback report with the team by EOD
                
                ## NEXT STEPS
                Schedule a follow-up meeting on Friday to review progress and address any new blockers.
                """)
                
                # Show option to save summary
                os.makedirs("Summaries", exist_ok=True)
                summary_path = os.path.join("Summaries", f"{selected_file.replace('.json', '')}_summary.md")
                st.success(f"Summary would be saved to: {summary_path}")
    else:
        st.info("No transcript files found to summarize. Please process transcripts first.")

# Add CSS for better styling
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True) 