from pydub import AudioSegment
import os
import sys
import subprocess
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Convert MP3 to WAV format')
parser.add_argument('--file', type=str, help='Path to the MP3 file', required=False)
args = parser.parse_args()

# Get the absolute path to the current directory
current_dir = os.getcwd()

# Set the path to the ffmpeg executable with absolute path
ffmpeg_dir = os.path.join(current_dir, "ffmpeg-master-latest-win64-gpl-shared", 
                         "ffmpeg-master-latest-win64-gpl-shared", "bin")
ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg.exe")
ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe.exe")

# Check if ffmpeg exists at the specified path
if not os.path.exists(ffmpeg_path):
    print(f"Error: ffmpeg not found at {ffmpeg_path}")
    print("Please download ffmpeg from https://github.com/BtbN/FFmpeg-Builds/releases")
    sys.exit(1)

# Tell pydub where to find ffmpeg and ffprobe
AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

# Add ffmpeg to the PATH environment variable
os.environ["PATH"] += os.pathsep + ffmpeg_dir

def get_ffmpeg_path():
    """Get the path to ffmpeg executable."""
    ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg-master-latest-win64-gpl-shared", 
                             "ffmpeg-master-latest-win64-gpl-shared", "bin")
    ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg.exe")
    
    if not os.path.exists(ffmpeg_path):
        print(f"Error: ffmpeg not found at {ffmpeg_path}")
        print("Please ensure ffmpeg is installed in the correct location.")
        sys.exit(1)
    
    return ffmpeg_path

def convert_mp3_to_wav(mp3_path, wav_path):
    try:
        # Check if MP3 file exists
        if not os.path.exists(mp3_path):
            print(f"Error: MP3 file not found at {mp3_path}")
            sys.exit(1)
        
        # Get ffmpeg path
        ffmpeg_path = get_ffmpeg_path()
        
        # Use subprocess directly for more control
        print(f"Converting {mp3_path} to {wav_path} using ffmpeg...")
        cmd = [ffmpeg_path, "-i", mp3_path, "-acodec", "pcm_s16le", "-ar", "44100", wav_path]
        subprocess.run(cmd, check=True)
        
        print(f"Successfully converted {mp3_path} to {wav_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during ffmpeg conversion: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        print("If the error is about ffmpeg, make sure you've installed it correctly.")
        sys.exit(1)

# Determine input file path
if args.file:
    # Use the file path provided as command-line argument
    mp3_file = args.file
    print(f"Using MP3 file from command-line argument: {mp3_file}")
else:
    # Use default path
    mp3_file = os.path.abspath(os.path.join("Audio", "videoplayback (1)-11.mp3"))
    print(f"Using default MP3 file: {mp3_file}")

# Print current directory for debugging
print(f"Current directory: {os.getcwd()}")
print(f"Looking for MP3 file at: {mp3_file}")
print(f"Using ffmpeg at: {ffmpeg_path}")
print(f"Using ffprobe at: {ffprobe_path}")

# Check if MP3 file exists before proceeding
if not os.path.exists(mp3_file):
    print(f"Error: MP3 file not found at {mp3_file}")
    print(f"Contents of Audio directory: {os.listdir('Audio') if os.path.exists('Audio') else 'Audio directory not found'}")
    sys.exit(1)

# Make sure the output directory exists
os.makedirs("WAV_Audio", exist_ok=True)

# Get the original filename without extension and use it for the output WAV file
mp3_filename = os.path.basename(mp3_file)
wav_filename = os.path.splitext(mp3_filename)[0] + ".wav"
wav_file = os.path.abspath(os.path.join("WAV_Audio", wav_filename))

convert_mp3_to_wav(mp3_file, wav_file)