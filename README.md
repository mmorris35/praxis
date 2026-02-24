# Praxis

**A system for creating expert systems.**

Praxis turns dense documentation into actionable expertise — not a chatbot that quotes manuals, but an expert that knows what actually works and learns from every refinement.

## The Pattern

Every complex field has the same problem: mountains of documentation that takes years to master. Praxis solves this with a three-layer architecture:

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: Refinements                                   │
│  └─ Learns from use — the flywheel                      │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: Institutional Knowledge (optional)            │
│  └─ Your org's expertise on top of the docs             │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: Foundation                                    │
│  └─ Structured domain docs — commodity                  │
└─────────────────────────────────────────────────────────┘
```

### Layer 1: Foundation
Structured ingestion of official documentation. Use OSCAL JSON, not PDFs. One concept per chunk. Proper metadata.

### Layer 2: Institutional Knowledge *(optional)*
Your org's expertise on top of the docs — API mappings, practical shortcuts, what actually works. Not required; you can start with Foundation + Refinements and learn from use.

### Layer 3: Refinements
AMP (Agent Memory Protocol) integration via Nellie. Experts refine responses, and those refinements persist for every future query.

The more the system is used, the smarter it gets.

## Technical Stack

- **Embeddings**: nomic-embed-text via Ollama
- **Vector DB**: ChromaDB
- **RAG**: Hybrid search (exact ID match + semantic)
- **LLM**: Claude/GPT for response generation
- **Memory**: Nellie-RS (AMP implementation)

## Examples

### J-Mo (Mortgage Underwriting Compliance)
Mortgage underwriting assistant for agency guidelines (Fannie, Freddie, FHA, VA). Needs Layer 1 foundation data (selling guides, HUD 4000.1) and Layer 2 expert translation (what underwriters actually check, common suspension reasons, condition clearing).

See [examples/jmo](./examples/jmo/)

### CMMC-Buddy
Complete CMMC Level 2 compliance assistant with:
- 1,955 framework controls (800-53, 800-171, CSF, FedRAMP)
- 320 CMMC objectives mapped to Microsoft Graph API calls
- PowerShell and curl commands for evidence collection
- Assessment guidance, common gaps, and assessor tips

See [examples/cmmc-buddy](./examples/cmmc-buddy/)

## Quick Start

```bash
# Clone
git clone git@github.com:mmorris35/praxis.git
cd praxis

# Set up an example
cd examples/cmmc-buddy
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp config/gateway.yaml.template config/gateway.yaml
# Edit with your API keys

# Ingest data
python -m ingest.ingest_full

# Run
uvicorn gateway.main:app --host 0.0.0.0 --port 8081
```

## Applicable Domains

The Praxis pattern works for any field with:
- Dense official documentation
- Expert knowledge required for practical application
- Real-world edge cases that improve with refinements

Examples:
- **Compliance**: CMMC, HIPAA, SOC 2, ISO 27001, PCI-DSS
- **Regulatory**: FDA, EPA, OSHA, financial regulations
- **Legal**: Case law research, contract analysis
- **Technical**: Engineering standards, building codes
- **Medical**: Clinical guidelines, diagnostic support

## License

Proprietary. All rights reserved.

## Author

Mike Morris
