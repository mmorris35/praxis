# Praxis

**A system for creating expert systems.**

Praxis turns dense documentation into actionable expertise — not a chatbot that quotes manuals, but an expert that knows what actually works and learns from every correction.

## The Pattern

Every complex field has the same problem: mountains of documentation that takes years to master. Praxis solves this with a three-layer architecture:

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: Corrections (AMP/Nellie)                      │
│  └─ Self-improving via real-world use                   │
│     The flywheel that compounds value over time         │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: Expert Translation                            │
│  └─ "How to actually do it" mappings                    │
│     The moat — takes years of expertise to build        │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: Foundation Data                               │
│  └─ Structured domain knowledge (OSCAL, specs, regs)    │
│     Commodity — anyone can ingest documentation         │
└─────────────────────────────────────────────────────────┘
```

### Layer 1: Foundation
Structured ingestion of official documentation. Use OSCAL JSON, not PDFs. One concept per chunk. Proper metadata.

### Layer 2: Expert Translation
The hard part. Maps theoretical requirements to practical implementation:
- What does an assessor *actually* want to see?
- What API calls gather the evidence?
- What documents do you need?
- What are the common gaps?

This layer is the moat — it takes domain expertise and years of real-world experience to build.

### Layer 3: Corrections
AMP (Agent Memory Protocol) integration via Nellie. When the system gets something wrong, experts can correct it. Those corrections persist and improve every future response.

The more the system is used, the smarter it gets.

## Technical Stack

- **Embeddings**: nomic-embed-text via Ollama
- **Vector DB**: ChromaDB
- **RAG**: Hybrid search (exact ID match + semantic)
- **LLM**: Claude/GPT for response generation
- **Memory**: Nellie-RS (AMP implementation)

## Examples

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
- Real-world edge cases that improve with corrections

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
