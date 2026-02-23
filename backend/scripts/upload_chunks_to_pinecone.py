import json
import os
import sys

# Add the parent directory to sys.path to import from app/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.embeddings.embedder import embed_texts
from app.vectorstore.pinecone_client import upsert_embeddings, check_existing_ids

# Load chunks from JSON file
chunks_file = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "chunks_data.json"
)

print("📂 Loading chunks from chunks_data.json...")
with open(chunks_file, "r", encoding="utf-8") as f:
    data = json.load(f)

chunks_data = data["chunks"]
print(f"✅ Loaded {len(chunks_data)} chunks\n")

# Get existing IDs from Pinecone
print("🔍 Checking for existing chunks in Pinecone...")
all_chunk_ids = [chunk["chunk_id"] for chunk in chunks_data]
existing_ids = check_existing_ids(all_chunk_ids)
print(f"✅ Found {len(existing_ids)} existing chunks in Pinecone\n")

# Filter out chunks that already exist
chunks_to_upload = [
    chunk for chunk in chunks_data 
    if chunk["chunk_id"] not in existing_ids
]

if len(chunks_to_upload) == 0:
    print("✨ All chunks are already uploaded to Pinecone!")
    print(f"   Total chunks in database: {len(existing_ids)}")
    sys.exit(0)

print(f"📊 Upload Summary:")
print(f"   Total chunks in file: {len(chunks_data)}")
print(f"   Already in Pinecone: {len(existing_ids)}")
print(f"   New chunks to upload: {len(chunks_to_upload)}\n")

# Extract text content for embedding
texts = [chunk["content"] for chunk in chunks_to_upload]

print("🔄 Generating embeddings...")
embeddings = embed_texts(texts)
print(f"✅ Generated {len(embeddings)} embeddings\n")

# Prepare vectors for Pinecone
vectors = []
for chunk, embedding in zip(chunks_to_upload, embeddings):
    vectors.append((
        chunk["chunk_id"],
        embedding,
        {
            "text": chunk["content"],
            "source": chunk["url"],
            "title": chunk["title"],
            "chunk_index": chunk["chunk_index"]
        }
    ))

print(f"📤 Uploading {len(vectors)} vectors to Pinecone...")

# Batch upsert (Pinecone recommends batches of 100)
BATCH_SIZE = 100
for i in range(0, len(vectors), BATCH_SIZE):
    batch = vectors[i:i+BATCH_SIZE]
    upsert_embeddings(batch)
    print(f"  ✓ Uploaded batch {i//BATCH_SIZE + 1} ({len(batch)} vectors)")

print(f"\n✅ Successfully uploaded {len(vectors)} new chunks to Pinecone!")
print(f"   Index: {os.getenv('PINECONE_INDEX_NAME')}")
print(f"   Total chunks in Pinecone: {len(existing_ids) + len(vectors)}")
print(f"   Previously existing: {len(existing_ids)}")
print(f"   Newly added: {len(vectors)}")
