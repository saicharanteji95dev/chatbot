import uuid
import os
import sys
import json
from datetime import datetime

# Add the parent directory to sys.path to import from app/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.ingestion.scraper import scrape_url
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import chunk_text

# ---------------- Load URLs ---------------- #

urls_file = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "urls.txt"
)

if not os.path.exists(urls_file):
    print("❌ urls.txt not found")
    sys.exit(1)

URLS = []
with open(urls_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            URLS.append(line)

if not URLS:
    print("❌ No valid URLs found in urls.txt")
    sys.exit(1)

print(f"✅ Found {len(URLS)} URL(s) to process\n")

# ---------------- Regenerate Chunks ---------------- #

all_chunks_data = []

for url in URLS:
    print(f"🔗 Processing: {url}")

    try:
        scraped_data = scrape_url(url)
        raw_text = scraped_data['text']

        if not raw_text or len(raw_text.strip()) < 500:
            print("⚠️ Skipping page (not enough content)\n")
            continue

        clean_text_data = clean_text(raw_text)
        chunks = chunk_text(clean_text_data)

        if not chunks:
            print("⚠️ No chunks generated, skipping\n")
            continue

        for idx, text in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            
            # Store chunk data for JSON export
            all_chunks_data.append({
                "chunk_id": chunk_id,
                "url": url,
                "title": scraped_data['title'],
                "headings": [{"level": "h1", "text": scraped_data['title']}],  # Simplified headings
                "content": text,
                "tables": scraped_data['tables'],
                "chunk_index": idx
            })

        print(f"✅ Generated {len(chunks)} chunks\n")

    except Exception as e:
        print(f"❌ Error processing {url}: {str(e)}\n")

# ---------------- Save to JSON ---------------- #

output_file = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "chunks_data.json"
)

output_data = {
    "metadata": {
        "total_chunks": len(all_chunks_data),
        "total_urls": len(URLS),
        "created_at": datetime.now().isoformat(),
        "urls": URLS
    },
    "chunks": all_chunks_data
}

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Successfully saved {len(all_chunks_data)} chunks to chunks_data.json")
