import os
import json
import glob
from datetime import datetime
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Process transcript files and save as JSON')
parser.add_argument('--file', type=str, help='Path to the audio file (to find matching transcript)', required=False)
args = parser.parse_args()

def process_transcript_file(transcript_file):
    """Process a single transcript file and return structured data."""
    # Extract base filename (without path and extension)
    base_filename = os.path.splitext(os.path.basename(transcript_file))[0]
    
    print(f"Processing transcript: {base_filename}")
    
    # Read the transcript file
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    
    # Parse the transcript into structured data
    transcript_data = []
    for line in transcript_text.split('\n'):
        if line.strip():
            try:
                # Check if line matches timestamp format [HH:MM:SS]
                if line.startswith('[') and ']' in line:
                    # Extract timestamp, which is in format [HH:MM:SS]
                    timestamp_part = line.split(']')[0] + ']'
                    timestamp_str = timestamp_part[1:-1]  # Remove the brackets
                    
                    # Try to parse the timestamp
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%H:%M:%S")
                        
                        # Extract the content after the timestamp
                        content = line[len(timestamp_part):].strip()
                        
                        # Split speaker and message
                        if ': ' in content:
                            speaker, message = content.split(': ', 1)
                            
                            # Create record
                            record = {
                                "timestamp": timestamp_str,
                                "speaker": speaker,
                                "text": message
                            }
                            transcript_data.append(record)
                    except ValueError as e:
                        print(f"Error parsing timestamp '{timestamp_str}': {e}")
                        # Not a valid timestamp format, skip this line
                        continue
            except Exception as e:
                print(f"Error processing line: {line[:50]}... - {str(e)}")
                continue
    
    return transcript_data, base_filename

def save_to_json(data, filepath, filename):
    """Save data to a JSON file."""
    # Create directory if it doesn't exist
    os.makedirs(filepath, exist_ok=True)
    
    # Create JSON file path
    json_path = os.path.join(filepath, f"{filename}.json")
    
    # Save data as JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return json_path

# Main execution
if __name__ == "__main__":
    if args.file:
        # Get the base filename from the command-line argument
        input_path = args.file
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        transcript_file = os.path.join("TEXT_Transcripts", f"{base_name}_transcript.txt")
        
        if os.path.exists(transcript_file):
            print(f"Processing transcript from command-line argument: {transcript_file}")
            transcript_files = [transcript_file]
        else:
            print(f"Transcript file not found for {base_name}, looking for all transcript files")
            transcript_files = glob.glob("TEXT_Transcripts/*_transcript.txt")
    else:
        # Find all transcript files in the TEXT_Transcripts directory
        transcript_files = glob.glob("TEXT_Transcripts/*_transcript.txt")
    
    if not transcript_files:
        print("No transcript files found in TEXT_Transcripts directory!")
    else:
        print(f"Found {len(transcript_files)} transcript files")
        
        # Process each transcript file
        for transcript_file in transcript_files:
            # Process the transcript and get structured data
            transcript_data, base_filename = process_transcript_file(transcript_file)
            
            if transcript_data:
                print(f"Processed {len(transcript_data)} segments from {base_filename}")
                
                # Save the data to JSON
                filepath = "JSON_Transcripts"
                json_path = save_to_json(transcript_data, filepath, base_filename)
                print(f"Data saved to {json_path}")
            else:
                print(f"No valid transcript data found in {transcript_file}")
        
        print("\nAll transcripts processed and saved as JSON!") 