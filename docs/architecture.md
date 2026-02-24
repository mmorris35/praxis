# Praxis Architecture

## Overview

Praxis is a framework for building domain-specific expert systems that combine:
1. Structured knowledge (RAG)
2. Expert translation (the "how to actually do it")
3. Self-improvement via refinements (AMP)

## The Three Layers

### Layer 1: Foundation Data

**Purpose**: Ingest and structure official domain documentation.

**Key Principles**:
- Use structured formats (JSON, OSCAL) over PDFs when available
- One concept per chunk (one control, one objective, one requirement)
- Rich metadata (source, section, ID, title, family)
- Dual ID formats when applicable (e.g., OSCAL + traditional numbering)

**Example (CMMC)**:
- NIST 800-53 Rev 5: 1,196 controls from OSCAL JSON
- NIST 800-171 Rev 3: 130 controls with 800-53 mappings
- NIST CSF 2.0: 219 controls
- FedRAMP HIGH: 410 controls

**This layer is commodity** — anyone with technical skills can ingest documentation.

### Layer 2: Expert Translation

**Purpose**: Map theoretical requirements to practical implementation.

**What it contains**:
- What assessors/auditors actually want to see
- Specific technical steps (API calls, commands, queries)
- Required documentation beyond technical evidence
- Common gaps and failure modes
- Tips from real-world experience

**Example (CMMC)**:
- 320 CMMC L2 objectives mapped to Microsoft Graph API endpoints
- Each objective includes: assessor expectations, API calls with purpose, manual docs needed, common gaps, tips
- 826 total API references across objectives

**This layer is the moat** — it takes years of domain expertise to build correctly.

### Layer 3: Refinement (AMP)

**Purpose**: Continuous improvement via expert feedback.

**How it works**:
1. User asks a question
2. System retrieves context and generates response
3. If response is wrong, expert submits refinement
4. Refinement stored in Nellie with semantic indexing
5. Future queries recall relevant refinements as "institutional knowledge"
6. Refinements take priority over raw documentation

**Why it matters**:
- Documentation has gaps, ambiguities, edge cases
- Real-world usage reveals what matters
- Refinements compound — each one improves the system
- Creates a flywheel that competitors can't easily replicate

## Technical Components

### RAG (Retrieval-Augmented Generation)

```
Query → Hybrid Search → Context Assembly → LLM → Response
           ↓
    ┌──────┴──────┐
    │ Exact Match │ → Control IDs, objective refs
    │ (priority)  │
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │  Semantic   │ → Conceptual similarity
    │   Search    │
    └─────────────┘
```

**Embeddings**: nomic-embed-text via Ollama (768 dimensions)
- Better than ChromaDB default for technical content
- Local/self-hosted option available

**Vector DB**: ChromaDB
- Persistent storage
- Metadata filtering
- Good enough for most use cases

### AMP (Agent Memory Protocol)

Integration with Nellie-RS for:
- `recall(query)` — find relevant refinements before inference
- `learn(question, refinement, original)` — store new refinements
- Semantic search over refinements
- Tags and severity for prioritization

### LLM Layer

Configurable backend (Claude, GPT, local models).

System prompt instructs:
- Prioritize institutional knowledge (refinements)
- Cite sources properly
- Format technical output (code blocks, commands)
- Admit when context doesn't contain the answer

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      USER QUERY                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AMP PRE-RECALL                           │
│              (Check for relevant refinements)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     RAG RETRIEVAL                           │
│         (Hybrid search: exact + semantic)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   CONTEXT ASSEMBLY                          │
│        (Refinements + Framework chunks + Expert layer)      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      LLM INFERENCE                          │
│            (Generate response with citations)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       RESPONSE                              │
│          (With sources, ready for refinement)               │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │    User submits refinement │
              └─────────────┬─────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      AMP LEARN                              │
│            (Store refinement for future recall)             │
└─────────────────────────────────────────────────────────────┘
```

## Building a New Expert System

1. **Identify the domain** — Dense documentation + expertise gap
2. **Gather foundation data** — Official sources, structured formats preferred
3. **Build expert layer** — This is the hard part. Interview experts, document real procedures, map theory to practice.
4. **Configure Praxis** — Set up ingestion, embeddings, LLM
5. **Ingest and test** — Load data, verify retrieval quality
6. **Deploy with refinements enabled** — Let real usage improve the system
7. **Iterate** — Review refinements, update expert layer, re-ingest

## Deployment Models

### SaaS
- Multi-tenant, shared refinements pool
- Lower friction, recurring revenue
- Refinements benefit all users (network effect)

### On-Premises / Private
- Single-tenant, private refinements
- Higher price point
- Organizations keep their refinements private
- Appeals to security-conscious buyers

### Hybrid
- Free tier: Foundation only (Layer 1)
- Pro tier: Foundation + Expert (Layers 1-2)
- Enterprise: Private deployment, keep refinements (All layers, isolated)
