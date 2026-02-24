
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Create index if it doesn't exist
if INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating Pinecone index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,  # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    print(f"✅ Index '{INDEX_NAME}' created successfully")

index = pc.Index(INDEX_NAME)

def upsert_embeddings(vectors):
    index.upsert(vectors=vectors)

def query_embedding(vector, top_k=5):
    return index.query(vector=vector, top_k=top_k, include_metadata=True)

def check_existing_ids(chunk_ids):
    """Check which chunk IDs already exist in Pinecone"""
    if not chunk_ids:
        return set()
    
    existing_ids = set()
    
    # Pinecone fetch supports up to 1000 IDs at a time
    BATCH_SIZE = 1000
    
    for i in range(0, len(chunk_ids), BATCH_SIZE):
        batch_ids = chunk_ids[i:i+BATCH_SIZE]
        try:
            # Fetch vectors by ID - returns only IDs that exist
            result = index.fetch(ids=batch_ids)
            existing_ids.update(result.get('vectors', {}).keys())
        except Exception as e:
            print(f"⚠️  Warning: Error checking batch {i//BATCH_SIZE + 1}: {e}")
            # On error, assume none exist in this batch
            continue
    
    return existing_ids
