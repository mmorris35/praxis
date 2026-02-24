# AMP Gateway — Build Plan

## Goal
A working demo that Mike's wife can sit in front of, ask mortgage underwriting questions,
and get accurate answers with guideline citations — all flowing through an observable
AI gateway with AMP-powered institutional memory.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    amp-gateway                        │
│                                                      │
│  FastAPI (OpenAI-compatible /v1/chat/completions)    │
│                                                      │
│  Pipeline:                                           │
│  1. Auth (API key)                                   │
│  2. AMP Recall (query Nellie for relevant lessons)   │
│  3. RAG Retrieve (ChromaDB — guideline chunks)       │
│  4. Prompt Assembly (user query + AMP + RAG)         │
│  5. LLM Route (Anthropic/OpenAI/Ollama)              │
│  6. Quality Check (grounding score)                  │
│  7. AMP Learn (checkpoint update, refinement capture)│
│  8. Trace (OpenTelemetry spans + audit log)          │
│                                                      │
│  No sanitization layer needed — zero PII in this     │
│  use case. Layer exists but disabled by default.     │
└──────────────────────────────────────────────────────┘
```

## Phase 1: Document Ingestion (Day 1)
- [ ] Download all 5 primary source PDFs
- [ ] PDF → text extraction (PyMuPDF or pdfplumber)
- [ ] Chunking strategy: by section/subsection (preserve guideline structure)
- [ ] Each chunk tagged with: source (Fannie/Freddie/FHA/VA/USDA), section number, page
- [ ] Load into ChromaDB with embeddings
- [ ] Verify: simple similarity search returns relevant chunks

### Chunking Strategy
Mortgage guidelines are heavily structured (sections, subsections, numbered items).
Chunk boundaries should respect this structure:
- Split on section headers (e.g., "B3-3.1-01: General Income Information")
- Keep parent section context in chunk metadata
- Overlap: include parent section title in each child chunk
- Target chunk size: ~500-800 tokens (enough context, not too diluted)

## Phase 2: Core Gateway (Day 1-2)
- [ ] FastAPI app with pipeline engine
- [ ] OpenAI-compatible API endpoint (/v1/chat/completions)
- [ ] Config-driven pipeline (gateway.yaml)
- [ ] RAG layer: query ChromaDB, return top-K chunks with metadata
- [ ] Prompt assembly: system prompt + RAG chunks (with citations) + user query
- [ ] LLM routing: configurable backend (start with Anthropic Claude)
- [ ] Response includes citations (source doc, section, page)

## Phase 3: AMP Integration (Day 2-3)
- [ ] AMP Recall layer: query Nellie for lessons relevant to the query
- [ ] AMP Learn layer: 
  - Auto-checkpoint conversation state
  - Capture refinements ("actually, the limit is X not Y")
  - Record common confusion points as lessons
- [ ] Agent scoping: one shared agent for the team to start

## Phase 4: Observability (Day 3)
- [ ] OpenTelemetry tracing across all pipeline stages
- [ ] Audit log: every request/response logged with trace ID
- [ ] Simple web dashboard showing:
  - Recent queries and responses
  - Pipeline timing breakdown
  - AMP lessons accumulated
  - RAG retrieval quality (relevance scores)

## Phase 5: Chat UI (Day 3-4)
- [ ] Simple web chat interface (can be very basic)
- [ ] Shows responses with expandable citations
- [ ] Shows which AMP lessons were used
- [ ] "This is wrong" button → triggers AMP lesson creation
- [ ] Conversation history within session

## Phase 6: Polish & Demo Prep (Day 4-5)
- [ ] Pre-populate 5-10 AMP lessons from common underwriting Q&A
- [ ] Test with real underwriting questions
- [ ] Ensure citations are accurate
- [ ] Docker-compose for one-command startup
- [ ] README with demo walkthrough

## Tech Stack
| Component | Choice | Why |
|---|---|---|
| Gateway | Python / FastAPI | Fastest to build, huge AI ecosystem |
| Vector DB | ChromaDB | Simple, embedded, good enough for demo |
| Embeddings | OpenAI text-embedding-3-small or local | Fast, cheap, good quality |
| LLM | Anthropic Claude (via API) | Best for long-context guideline Q&A |
| AMP Server | Nellie (already running) | We have it, it works |
| PDF Extraction | PyMuPDF (fitz) | Best PDF text extraction |
| Observability | OpenTelemetry + simple SQLite log | Lightweight, self-contained |
| Chat UI | Simple HTML/JS or Gradio | Demo-quality, not production |
| Deployment | Docker Compose | One command to run |

## File Structure
```
projects/amp-gateway/
├── docker-compose.yml
├── gateway/
│   ├── main.py                 # FastAPI app
│   ├── pipeline.py             # Middleware pipeline engine
│   ├── config.py               # YAML config loader
│   ├── layers/
│   │   ├── auth.py             # API key auth
│   │   ├── sanitizer.py        # PII (disabled for this demo)
│   │   ├── amp_recall.py       # Pre-inference AMP query
│   │   ├── rag.py              # ChromaDB retrieval
│   │   ├── assembler.py        # Prompt assembly
│   │   ├── router.py           # LLM backend routing
│   │   ├── quality.py          # Grounding check
│   │   ├── amp_learn.py        # Post-inference learning
│   │   └── trace.py            # OpenTelemetry + audit
│   └── models.py               # Request/response models
├── ingest/
│   ├── download.py             # Fetch all source PDFs
│   ├── extract.py              # PDF → text
│   ├── chunk.py                # Text → structured chunks
│   └── load.py                 # Chunks → ChromaDB
├── ui/
│   ├── index.html              # Chat interface
│   └── app.js                  # Chat logic
├── config/
│   └── gateway.yaml            # Pipeline configuration
├── data/
│   ├── pdfs/                   # Downloaded source documents
│   └── chroma/                 # ChromaDB storage
├── tests/
├── requirements.txt
├── Dockerfile
├── SOURCES.md                  # Document catalog
├── BUILD_PLAN.md               # This file
└── README.md
```

## Demo Script
1. Start everything: `docker-compose up`
2. Open chat UI: `http://localhost:8080`
3. Ask: "What's the minimum credit score for an FHA loan?"
   → Answer with HUD 4000.1 citation
4. Ask: "What about for VA?"
   → Answer noting VA has no minimum, with Pamphlet 26-7 citation
5. Say: "Actually, for FHA, there's a distinction between 580+ for 3.5% down and 500-579 for 10% down"
   → AMP captures the refinement as a lesson
6. Ask the same FHA credit score question again
   → Now includes the nuanced answer (AMP lesson recalled)
7. Show the audit dashboard: every query traced, timing visible, lessons accumulating
8. Profit
