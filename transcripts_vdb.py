from pinecone import Pinecone, ServerlessSpec
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
import json
from pinecone.grpc import PineconeGRPC as Pinecone
import glob

PINECONE_API_KEY="pcsk_3zChdB_EwSrLamw7HJ4KjNQo7kTadocgcqaUBbXcbQcFomoUAPy52UnGRJu5XBbfL94cQb"


# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Initialize the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dimensional embeddings

# Create a dense index for meeting transcripts
index_name = "meeting-transcripts"

# Create index without integrated inference
if not pc.has_index(index_name):
    pc.create_index(
        name=index_name,
        dimension=384,  # Matches the SentenceTransformer model's output
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

def process_transcript_file(transcript_file):
    """Process a single transcript file and return records for Pinecone."""
    # Extract base filename (without path and extension)
    base_filename = os.path.splitext(os.path.basename(transcript_file))[0]
    
    print(f"Processing transcript: {base_filename}")
    
    # Read the transcript file
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_text = f.read()

# Parse and prepare records with embeddings
    records = []
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
                        
                        # Generate embedding for the message
                        embedding = model.encode(message)
                        
                        # Create record with unique ID, metadata, and embedding
                        record = {
                                "id": f"{base_filename}_msg_{len(records)}",
                            "values": embedding.tolist(),  # The embedding vector
                            "metadata": {
                                "timestamp": timestamp_str,
                                "speaker": speaker,
                                "message": message,
                                    "source_file": base_filename,
                                "category": "meeting_transcript"
                            }
                        }
                        records.append(record)
                except ValueError:
                    # Not a valid timestamp format, skip this line
                    continue
            except Exception as e:
                print(f"Error processing line: {line[:50]}... - {str(e)}")
            continue

    return records, base_filename

def search_transcripts(query, top_k=3):
    # Example search query
    query_embedding = model.encode(query)
    
    # Search the index
    search_results = dense_index.query(
        namespace="meeting-namespace",
        vector=query_embedding.tolist(),
        top_k=top_k,
        include_metadata=True
    )

    # Print results
    for result in search_results['matches']:
        print(f"Score: {result['score']}")
        print(f"Message: {result['metadata']['message']}")
        print("---")
    
    return search_results

def fetch_metadata_only(index_host, namespace, ids):
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Connect to the index using its host
    index = pc.Index(host=index_host)
    
    # Fetch the vectors with their metadata
    result = index.fetch(ids=ids, namespace=namespace)
    
    # Extract only the metadata from the result
    metadata_only = {}
    for vector_id, vector_data in result.vectors.items():
        metadata_only[vector_id] = vector_data.get('metadata', {})
    
    return metadata_only

def list_ids(host, namespace):
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Connect to the index using its host
    index = pc.Index(host=host)

    ids = []
    for id in index.list(namespace=namespace):
        # print(id)
        ids += id
    
    return ids

def save_metadata_to_json(metadata, filepath, filename):
    # Create directory with audio filename if it doesn't exist
    directory = filepath  # e.g., "audio1"
    os.makedirs(directory, exist_ok=True)
    
    # Create JSON file path
    json_path = os.path.join(directory, f"{filename}.json")
    
    # Save metadata as JSON
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return json_path

# Example usage
if __name__ == "__main__":
    # Target the index
    dense_index = pc.Index(index_name)
    namespace = "meeting-namespace"
    
    # Find all transcript files in the TEXT_Transcripts directory
    transcript_files = glob.glob("TEXT_Transcripts/*_transcript.txt")
    
    if not transcript_files:
        print("No transcript files found in TEXT_Transcripts directory!")
    else:
        print(f"Found {len(transcript_files)} transcript files")
        
        # Process each transcript file
        for transcript_file in transcript_files:
            # Process the transcript and get records
            records, base_filename = process_transcript_file(transcript_file)
            
            if records:
                print(f"Generated {len(records)} records for {base_filename}")
                
                # Upsert the records into Pinecone
                upsert_response = dense_index.upsert(vectors=records, namespace=namespace)
                
                # Handle the response based on Pinecone client version
                try:
                    # For older Pinecone client versions that return a dict
                    print(f"Upserted count: {upsert_response['upserted_count']}")
                except TypeError:
                    # For newer Pinecone client versions that return an object
                    print(f"Upserted count: {upsert_response.upserted_count}")
                    
                # Save the metadata to JSON as well
                host = "https://meeting-transcripts-dwfsxz0.svc.aped-4627-b74a.pinecone.io"
                
                # List IDs for this specific file
                # This is a simple way to filter - in a real application you might want
                # to use a more robust approach like filtering in the fetch call
                all_ids = list_ids(host, namespace)
                file_ids = [id for id in all_ids if id.startswith(f"{base_filename}_msg_")]
                
                if file_ids:
    # Fetch metadata
                    metadata = fetch_metadata_only(host, namespace, file_ids)
    
    # Save metadata to JSON
    filepath = "JSON_Transcripts"
    json_path = save_metadata_to_json(metadata, filepath, base_filename)
    print(f"Metadata saved to {json_path}")
    
else:
    print(f"No valid records found in {transcript_file}")
        
    print("\nAll transcripts processed and uploaded to Pinecone!") 


