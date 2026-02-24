# Backend Flow Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Data Ingestion Pipeline](#data-ingestion-pipeline)
3. [RAG (Retrieval Augmented Generation) Flow](#rag-retrieval-augmented-generation-flow)
4. [Query Processing Flow](#query-processing-flow)
5. [Configuration & Parameters](#configuration--parameters)
6. [API Endpoints](#api-endpoints)
7. [Technology Stack](#technology-stack)
8. [Performance Considerations](#performance-considerations)

---

## Architecture Overview

The i95Dev Chatbot backend follows a **RAG (Retrieval Augmented Generation)** architecture that combines:
- **Vector Search** for semantic retrieval
- **Large Language Models** for response generation
- **Context-aware memory** for conversational continuity

### High-Level Flow
```
User Query → API → Retrieval → Context → LLM → Streaming Response
              ↓                    ↓        ↓
         Embedding            Vector DB   Groq
```

### Core Components
```
backend/
├── app/
│   ├── api.py                    # FastAPI endpoints
│   ├── chatbot.py                # Chat orchestration
│   ├── embeddings/               # Text vectorization
│   ├── ingestion/                # Data pipeline
│   ├── llm/                      # LLM client (Groq)
│   ├── retrieval/                # Context retrieval
│   ├── vectorstore/              # Pinecone integration
│   ├── prompts/                  # System prompts
│   └── utils/                    # Configuration
└── scripts/
    ├── run_ingestion.py          # Batch data ingestion
    └── upload_chunks_to_pinecone.py  # Vector upload
```

---

## Data Ingestion Pipeline

The ingestion pipeline transforms web content into searchable vector embeddings through 5 stages:

### Stage 1: Web Scraping (`scraper.py`)
**Tool:** Playwright (headless Chromium browser)

**Process:**
1. **JavaScript Rendering:** Loads and executes JavaScript to access dynamic content
2. **Wait for Network Idle:** Ensures all resources are loaded
3. **OCR Image Extraction:**
   - Fetches images from `<img>` tags
   - Converts to grayscale using OpenCV
   - Applies threshold binary conversion (threshold: 150)
   - Extracts text via Tesseract OCR
   - Filters out images with < 15 characters
4. **HTML Parsing:** Uses BeautifulSoup4 to extract:
   - Page title
   - Headings (h1, h2, h3)
   - Blog content (`.wp-block-post-content`, `.entry-content`)
   - Service page blocks (`.wp-block-uagb-container`, `.uagb-container`)
5. **Noise Removal:** Strips `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, `<aside>`

**Output:**
```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "headings": [{"level": "h1", "text": "Heading"}],
  "sections": [{"header": "Title", "content": "Body text..."}],
  "images": ["Extracted OCR text..."]
}
```

---

### Stage 2: Text Cleaning (`cleaner.py`)

**Purpose:** Remove noise and fix encoding issues

**Key Operations:**
1. **UTF-8 Mojibake Fix:**
   - Detects double-encoding (UTF-8 bytes interpreted as Windows-1252)
   - Fixes common artifacts:
     - `â€™` → `'` (apostrophe)
     - `â€œ` → `"` (left quote)
     - `â€` → `"` (right quote)
     - `â€"` → `-` (em dash)
     - `Â ` → ` ` (non-breaking space)

2. **Unicode Normalization:**
   - Replaces `\xa0` and `\u00a0` with regular spaces
   
3. **Paragraph Filtering:**
   - Splits on `\n+` (newlines)
   - **Minimum paragraph length: 50 characters**
   
4. **Deduplication:**
   - Uses MD5 hashing to detect duplicate paragraphs
   - Prevents redundant content in chunks

5. **Whitespace Normalization:**
   - Collapses multiple spaces into single space

**Output:** Clean, deduplicated text ready for chunking

---

### Stage 3: Text Chunking (`chunker.py`)

**Strategy:** Paragraph-aware semantic chunking

**Parameters:**
- **Target chunk size:** 1200 characters
- **Minimum chunk size:** 300 characters
- **Overlap:** Natural (paragraph boundaries)

**Algorithm:**
```python
1. Split text into paragraphs (min 50 chars per paragraph)
2. Accumulate paragraphs until reaching target_size (1200)
3. If adding next paragraph exceeds target_size:
   - Save current chunk if ≥ min_chars (300)
   - Start new chunk with next paragraph
4. If chunk < min_chars, continue adding paragraphs
5. Preserve last chunk if ≥ min_chars
```

**Why Paragraph-Aware?**
- Maintains semantic context
- Prevents sentence splitting
- Improves retrieval relevance

**Chunk Metadata:**
```python
{
  "chunk_id": "uuid",
  "url": "source_url",
  "title": "page_title",
  "content": "chunk_text",
  "chunk_index": 0
}
```

---

### Stage 4: Embedding Generation (`embedder.py`)

**Model:** `all-MiniLM-L6-v2` (SentenceTransformers)

**Specifications:**
- **Embedding Dimension:** 384
- **Max Sequence Length:** 256 tokens
- **Architecture:** BERT-based
- **Performance:** ~6000 sentences/sec on CPU
- **Size:** 80MB

**Process:**
```python
texts → SentenceTransformer → 384-dimensional vectors
```

**Why all-MiniLM-L6-v2?**
- Lightweight and fast
- Good balance between speed and quality
- Works well for short-to-medium text (chunks ≤ 1200 chars)
- Multilingual support

---

### Stage 5: Vector Storage (`pinecone_client.py`)

**Vector Database:** Pinecone (Serverless)

**Index Configuration:**
- **Dimension:** 384 (matches embedding model)
- **Metric:** Cosine similarity
- **Cloud:** AWS
- **Region:** us-east-1

**Upload Process (`upload_chunks_to_pinecone.py`):**
1. **Load chunks** from `chunks_data.json`
2. **Check existing IDs** using `index.fetch()` (batch size: 1000)
3. **Filter new chunks** (skip already uploaded)
4. **Generate embeddings** for new chunks only
5. **Batch upsert** (100 vectors per batch)
6. **Metadata stored:**
   ```python
   {
     "text": "chunk_content",
     "source": "url",
     "title": "page_title",
     "chunk_index": 0
   }
   ```

**Deduplication Strategy:**
- Uses chunk_id (UUID generated from URL + chunk_index)
- Prevents duplicate uploads across runs

---

## RAG (Retrieval Augmented Generation) Flow

### Overview
RAG combines **retrieval** (finding relevant context) with **generation** (LLM response) to provide accurate, grounded answers.

```
User Query
    ↓
[1] Embed Query (384-dim vector)
    ↓
[2] Search Pinecone (Cosine Similarity)
    ↓
[3] Retrieve Top K Chunks (default: 4)
    ↓
[4] Combine Context
    ↓
[5] Send to LLM with System Prompt
    ↓
[6] Stream Response
```

---

### Step-by-Step RAG Process

#### **Step 1: Query Embedding** (`retriever.py`)
```python
query = "What services does i95Dev offer?"
query_vec = embed_texts([query])[0]  # 384-dim vector
```

#### **Step 2: Vector Search** (`pinecone_client.query_embedding()`)
```python
results = index.query(
    vector=query_vec,
    top_k=4,              # Retrieve top 4 chunks
    include_metadata=True
)
```

**Similarity Scoring:**
- **Metric:** Cosine similarity
- **Range:** -1.0 to 1.0
- **Typical scores:** 0.3 to 0.9+
- **Score interpretation:**
  - **> 0.7:** Highly relevant
  - **0.5 - 0.7:** Moderately relevant
  - **< 0.5:** Weakly relevant

**No Hard Threshold Applied:**
- Current implementation retrieves top_k regardless of score
- LLM prompt instructs: "Answer only if context is relevant"
- *Potential improvement:* Add score threshold (e.g., 0.4) to filter low-quality matches

#### **Step 3: Context Extraction** (`retriever.py`)
```python
contexts = []
for match in results["matches"]:
    score = match["score"]
    text = match["metadata"]["text"]
    source = match["metadata"]["source"]
    contexts.append(text)

context = "\n".join(contexts)  # Concatenate all chunks
```

**Debug Output (when DEBUG=True):**
```
======================================================================
🔍 TOP 4 RETRIEVED CHUNKS FOR QUERY:
❓ What services does i95Dev offer?
======================================================================

📌 Rank #1
Score   : 0.8456
Service : i95Dev
Source  : https://i95dev.com/services
Preview : i95Dev provides comprehensive B2B eCommerce solutions...

📌 Rank #2
Score   : 0.7821
...
```

**Multi-Service Warning:**
- If retrieved chunks span multiple services, logs a warning
- Helps detect potential context mixing issues

#### **Step 4: LLM Prompting** (`groq_client.py`)

**Message Structure:**
```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "system", "content": f"Relevant i95Dev context:\n{context}"},
    ...conversation_history...,
    {"role": "user", "content": query}
]
```

**Key System Prompt Rules:**
1. **Strict grounding:** Answer ONLY using provided context
2. **No inference:** Don't add info not in context
3. **Service isolation:** Don't mix info from different services
4. **Fallback response:** "I don't have that information..."
5. **No technical details:** Don't mention embeddings, vectors, etc.

**LLM Parameters:**
- **Model:** `llama-3.3-70b-versatile` (Groq)
- **Temperature:** 0.2 (low for consistency)
- **Streaming:** Token-by-token

#### **Step 5: Response Streaming** (`groq_client.stream_response()`)
```python
for chunk in completion:
    delta = chunk.choices[0].delta.content
    if delta:
        yield delta  # Stream to frontend
```

---

## Query Processing Flow

### Non-Streaming (`/chat` endpoint)
```
POST /chat
    ↓
Parse request messages
    ↓
Extract history + current query
    ↓
chatbot.chat(query, history)
    ↓
retrieve_context(query) → RAG
    ↓
generate_response() → LLM
    ↓
Return full response
```

### Streaming (`/chat/stream` endpoint)
```
POST /chat/stream
    ↓
Parse request messages
    ↓
Extract history + current query
    ↓
chatbot.chat_stream(query, history)
    ↓
retrieve_context(query) → RAG
    ↓
stream_response() → LLM (streaming)
    ↓
Yield tokens via StreamingResponse
```

**Streaming Benefits:**
- Faster perceived response time
- Better UX for long responses
- Reduced frontend timeout risk

---

## Configuration & Parameters

### Environment Variables (`.env`)
```bash
# Pinecone
PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=i95dev-chatbot

# Groq
GROQ_API_KEY=your_key

# CORS
FRONTEND_URL=http://localhost:3000
```

### Embedding Model
- **Model:** `all-MiniLM-L6-v2`
- **Dimensions:** 384
- **Max tokens:** 256

### Chunking Parameters
- **Target size:** 1200 characters
- **Min size:** 300 characters
- **Paragraph min:** 50 characters

### Retrieval Parameters
- **Top K:** 4 chunks
- **Similarity metric:** Cosine
- **No hard threshold** (relies on LLM filtering)

### LLM Parameters
- **Model:** `llama-3.3-70b-versatile`
- **Temperature:** 0.2
- **Streaming:** Enabled

### Pinecone Configuration
- **Metric:** Cosine
- **Dimension:** 384
- **Batch size (upsert):** 100
- **Batch size (fetch check):** 1000

---

## API Endpoints

### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "ok",
  "message": "i95Dev Chatbot API is running"
}
```

### `POST /chat`
Non-streaming chat endpoint

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "What services does i95Dev offer?"}
  ]
}
```

**Response:**
```json
{
  "role": "assistant",
  "content": "i95Dev provides..."
}
```

### `POST /chat/stream`
Streaming chat endpoint (token-by-token)

**Request:** Same as `/chat`

**Response:** `text/plain` stream
```
i95Dev
 provides
 comprehensive
...
```

**Frontend Integration:**
- Compatible with `assistant-ui` library
- Real-time token rendering

---

## Technology Stack

### Core Technologies
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI | REST API + streaming |
| **Embedding Model** | SentenceTransformers | Text → vectors |
| **Vector DB** | Pinecone | Semantic search |
| **LLM Provider** | Groq | Response generation |
| **LLM Model** | Llama 3.3 70B | Natural language responses |

### Ingestion Stack
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Scraping** | Playwright | JS rendering |
| **HTML Parsing** | BeautifulSoup4 | Content extraction |
| **OCR** | Tesseract + OpenCV | Image text extraction |
| **Text Processing** | Python regex | Cleaning & chunking |

### Infrastructure
- **Hosting:** Serverless (Pinecone)
- **CORS:** Multi-origin support
- **Environment:** Python 3.11+

---

## Performance Considerations

### Latency Breakdown (Typical Query)
```
Component                Time      %
─────────────────────────────────────
Query embedding          ~50ms     5%
Pinecone search          ~100ms    10%
Context retrieval        ~50ms     5%
LLM first token          ~500ms    50%
LLM streaming            ~300ms    30%
─────────────────────────────────────
TOTAL                    ~1000ms   100%
```

### Optimization Strategies

#### 1. **Retrieval Optimization**
- **Current:** Top K = 4 (balanced)
- **Low latency:** Top K = 2 (faster, less context)
- **High accuracy:** Top K = 8 (slower, more context)

#### 2. **Embedding Optimization**
- **Current:** CPU inference (~50ms)
- **Future:** GPU inference (~10ms)
- **Caching:** Store query embeddings for repeat questions

#### 3. **LLM Optimization**
- **Streaming:** Reduces perceived latency
- **Model selection:** Groq provides low-latency inference
- **Prompt length:** Keep context < 8K tokens

#### 4. **Vector DB Optimization**
- **Pinecone serverless:** Auto-scaling
- **Metadata filtering:** Add service/category filters
- **Index tuning:** Pod-based for high QPS (future)

### Scalability

**Current Limits:**
- **Pinecone serverless:** 100 QPS (queries per second)
- **Groq free tier:** 30 req/min (upgrade for production)
- **FastAPI:** Handles 1000+ concurrent connections

**Production Recommendations:**
1. **Add rate limiting** (e.g., 10 req/min per user)
2. **Implement caching** (Redis for common queries)
3. **Monitor costs** (Pinecone read units, Groq tokens)
4. **Add similarity threshold** (filter low-relevance chunks)

---

## Threshold Scores & Quality Control

### Current Implementation
- **No hard similarity threshold** applied during retrieval
- **Top K retrieval:** Always returns best 4 chunks (regardless of score)
- **Quality control:** Handled by LLM prompt instructions

### Observed Score Ranges
Based on production logs:
- **0.8 - 1.0:** Exact or near-exact match (rare)
- **0.6 - 0.8:** Highly relevant context
- **0.4 - 0.6:** Moderately relevant context
- **< 0.4:** Weak relevance (may need filtering)

### Recommended Threshold Strategy
```python
# Add to retriever.py
MIN_SCORE_THRESHOLD = 0.35

contexts = []
for match in results["matches"]:
    score = match["score"]
    if score < MIN_SCORE_THRESHOLD:
        continue  # Skip low-relevance chunks
    contexts.append(match["metadata"]["text"])

if not contexts:
    return "INSUFFICIENT_CONTEXT"  # Signal to LLM
```

**Benefits:**
- Prevents low-quality context pollution
- Reduces hallucination risk
- Improves response accuracy

---

## Future Enhancements

### Short-Term
1. **Add similarity threshold** (0.35 - 0.4)
2. **Implement query caching** (Redis)
3. **Add conversation persistence** (Supabase integration)
4. **Metadata filtering** (service, category)

### Medium-Term
1. **Hybrid search** (keyword + semantic)
2. **Re-ranking** (cross-encoder for top results)
3. **Query expansion** (synonyms, related terms)
4. **Multi-turn context window** (sliding window memory)

### Long-Term
1. **Fine-tuned embedding model** (domain-specific)
2. **Custom LLM fine-tuning** (i95Dev terminology)
3. **Multi-modal support** (images, PDFs)
4. **Analytics dashboard** (query metrics, scores)

---

## Troubleshooting

### Low Relevance Scores
**Symptoms:** All scores < 0.5
- **Cause:** Query embedding mismatch
- **Solution:** Check query preprocessing, try query expansion

### Duplicate Content
**Symptoms:** Same chunk retrieved multiple times
- **Cause:** Chunking overlap or scraping duplication
- **Solution:** Improve deduplication in `cleaner.py`

### Slow Response Times
**Symptoms:** > 3s total latency
- **Cause:** Network latency or cold start
- **Solution:** Check Pinecone region, use connection pooling

### Hallucinations
**Symptoms:** LLM adds info not in context
- **Cause:** Weak grounding or low-quality chunks
- **Solution:** Add threshold, strengthen system prompt

---

## Conclusion

This backend implements a production-ready RAG pipeline with:
- ✅ Robust data ingestion (scraping, cleaning, chunking)
- ✅ Semantic search via vector embeddings
- ✅ Contextual LLM responses with strict grounding
- ✅ Streaming support for better UX
- ✅ Scalable architecture (serverless vector DB)

**Key Strengths:**
- Paragraph-aware chunking preserves semantic context
- Cosine similarity provides reliable relevance scoring
- LLM prompt enforces strict answer grounding
- Streaming reduces perceived latency

**Recommended Next Steps:**
1. Add similarity threshold (0.35-0.4)
2. Implement query caching
3. Monitor and analyze score distributions
4. Fine-tune chunk size based on retrieval metrics

---

*Documentation generated: February 2026*  
*Version: 1.0*  
*Contact: i95Dev Technical Team*
