import torch
from pyannote.audio import Pipeline
import whisper
import os
import sys
import json
import soundfile as sf
import numpy as np
from datetime import timedelta
import argparse
import traceback
from dotenv import load_dotenv

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Transcribe audio with speaker diarization')
parser.add_argument('--file', type=str, help='Path to the audio file to transcribe', required=False)
parser.add_argument('--model', type=str, default='base', help='Whisper model size (tiny, base, small, medium, large)')
parser.add_argument('--hf_token', type=str, help='Hugging Face API token', required=False)
args = parser.parse_args()

# Load environment variables
load_dotenv()

# Get Hugging Face token from environment variable
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
if not HUGGINGFACE_TOKEN:
    raise ValueError("HUGGINGFACE_TOKEN not found in environment variables. Please set it in .env file.")

# Path to your audio file
if args.file:
    # Get the WAV file path from command-line argument (which might be an MP3 path)
    input_path = args.file
    # If input is an MP3 file, get the corresponding WAV file
    if input_path.lower().endswith('.mp3'):
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        AUDIO_FILE = os.path.join("WAV_Audio", f"{base_name}.wav")
    else:
        AUDIO_FILE = input_path
    print(f"Using audio file from command-line argument: {AUDIO_FILE}")
else:
    # Use the default path
    AUDIO_FILE = "WAV_Audio/videoplayback (1)-11.wav"
    print(f"Using default audio file: {AUDIO_FILE}")

# Check if the WAV file exists
if not os.path.exists(AUDIO_FILE):
    print(f"Error: Audio file not found at {AUDIO_FILE}")
    print(f"Contents of WAV_Audio directory: {os.listdir('WAV_Audio') if os.path.exists('WAV_Audio') else 'WAV_Audio directory not found'}")
    sys.exit(1)

print(f"Audio file exists and has size: {os.path.getsize(AUDIO_FILE)} bytes")

def format_timestamp(seconds):
    """Convert seconds to a [00:00:15] formatted timestamp"""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Function to load audio using soundfile
def load_audio(file_path, sr=16000):
    """Load an audio file and resample it to 16kHz (required by Whisper)"""
    print(f"Loading audio file: {file_path}")
    try:
        audio, sample_rate = sf.read(file_path)
        print(f"Audio loaded successfully. Sample rate: {sample_rate}Hz, Shape: {audio.shape}")
        
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)
            print(f"Converted stereo to mono. New shape: {audio.shape}")
        
        # Resample to 16kHz if needed
        if sample_rate != sr:
            print(f"Resampling from {sample_rate}Hz to {sr}Hz")
            # Simple resampling method
            duration = len(audio) / sample_rate
            new_length = int(duration * sr)
            audio = np.interp(
                np.linspace(0, len(audio), new_length),
                np.arange(len(audio)),
                audio
            )
            print(f"Resampling complete. New shape: {audio.shape}")
        
        # Normalize
        audio = audio / np.max(np.abs(audio))
        
        return audio.astype(np.float32)
    except Exception as e:
        print(f"Error loading audio file: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)

try:
    # Rest of the script - initialize diarization, transcription, etc.
    # Initialize the speaker diarization pipeline
    print("Loading speaker diarization pipeline...")
    diarization_pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=HUGGINGFACE_TOKEN
    )
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    diarization_pipeline.to(device)

    # Initialize the Whisper speech recognition model
    print(f"Loading Whisper speech recognition model: {args.model}")
    model = whisper.load_model(args.model)

    # Run speaker diarization
    print("Running speaker diarization...")
    diarization = diarization_pipeline(AUDIO_FILE)

    # Store the speaker segments
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        })
    print(f"Diarization complete. Found {len(segments)} speaker segments")

    # Load and prepare the audio
    print("Loading audio file for transcription...")
    audio = load_audio(AUDIO_FILE)

    # Run speech recognition
    print("Running speech recognition...")
    result = model.transcribe(audio)
    print(f"Transcription complete. Found {len(result['segments'])} segments")

    # Align the speaker diarization with the transcription segments
    print("Aligning speakers with transcription...")
    transcription = []
    for i, segment in enumerate(result["segments"]):
        # Find the dominant speaker for this segment
        segment_start = segment["start"]
        segment_end = segment["end"]
        segment_text = segment["text"].strip()
        
        # Skip empty segments
        if not segment_text:
            continue
        
        # Find overlapping speaker segments
        overlapping_speakers = []
        for s in segments:
            # Check if speaker segment overlaps with transcription segment
            if (s["end"] > segment_start and s["start"] < segment_end):
                overlap_start = max(s["start"], segment_start)
                overlap_end = min(s["end"], segment_end)
                overlap_duration = overlap_end - overlap_start
                overlapping_speakers.append((s["speaker"], overlap_duration))
        
        # Determine the dominant speaker (one with most overlap)
        if overlapping_speakers:
            dominant_speaker = max(overlapping_speakers, key=lambda x: x[1])[0]
        else:
            dominant_speaker = "UNKNOWN"
        
        # Use just the start timestamp for the transcript
        formatted_timestamp = format_timestamp(segment_start)
        
        # Add to final transcription
        transcription.append({
            "timestamp": formatted_timestamp,
            "speaker": dominant_speaker,
            "text": segment_text
        })

    # Create output directories if they don't exist
    os.makedirs("JSON_Transcripts", exist_ok=True)
    os.makedirs("TEXT_Transcripts", exist_ok=True)

    # Get the base filename from the audio file (without extension)
    base_filename = os.path.splitext(os.path.basename(AUDIO_FILE))[0]

    # Define output filenames with the audio filename
    txt_output_file = os.path.join("TEXT_Transcripts", f"{base_filename}_transcript.txt")
    json_output_file = os.path.join("JSON_Transcripts", f"{base_filename}_transcript.json")

    # Write the transcription to a text file
    print(f"Writing text transcript to {txt_output_file}")
    with open(txt_output_file, "w", encoding="utf-8") as f:
        for segment in transcription:
            f.write(f"[{segment['timestamp']}] {segment['speaker']}: {segment['text']}\n")

    # Save as JSON for easier processing
    print(f"Writing JSON transcript to {json_output_file}")
    with open(json_output_file, "w", encoding="utf-8") as f:
        json.dump(transcription, f, indent=2, ensure_ascii=False)

    print(f"Transcription complete! Output saved to:")
    print(f"- Text file: {txt_output_file}")
    print(f"- JSON file: {json_output_file}")
except Exception as e:
    print(f"Error during transcription process: {str(e)}")
    print(traceback.format_exc())
    sys.exit(1) 