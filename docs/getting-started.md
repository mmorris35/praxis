# Getting Started with Praxis

## Prerequisites

- Python 3.10+
- Ollama with `nomic-embed-text` model (for embeddings)
- Nellie-RS server (for AMP corrections)
- Claude or OpenAI API key

## Installation

```bash
git clone git@github.com:mmorris35/praxis.git
cd praxis
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running an Example

```bash
cd examples/cmmc-buddy

# Configure
export ANTHROPIC_API_KEY="your-key"
export OLLAMA_URL="http://localhost:11434"  # or your Ollama server
export NELLIE_URL="http://localhost:8765"   # or your Nellie server

# Ingest data
python -m core.ingest.ingest_full

# Run
uvicorn core.gateway.main:app --port 8081
```

## Creating a New Expert System

1. **Create example directory**
   ```bash
   mkdir -p examples/my-domain/data/structured
   mkdir -p examples/my-domain/ui
   mkdir -p examples/my-domain/config
   ```

2. **Gather foundation data (Layer 1)**
   - Find official structured data (JSON, XML, OSCAL)
   - Avoid PDFs if possible
   - One concept per chunk

3. **Build expert layer (Layer 2)**
   - Interview domain experts
   - Document practical procedures
   - Map theory to action
   - Include: what assessors want, common gaps, tips

4. **Create ingest script**
   - Parse your data format
   - Extract rich metadata
   - Load into ChromaDB with embeddings

5. **Configure and run**
   - Copy `core/config/gateway.yaml.template`
   - Set collection name, API keys
   - Run gateway

6. **Enable corrections**
   - Configure Nellie connection
   - Let real usage improve the system
