# JMO — The Original Praxis Proof of Concept

JMO (Just My Opinion) was the original implementation that proved the Praxis pattern works. It demonstrated:

1. RAG over compliance documentation
2. AMP corrections that persist and improve responses
3. The three-layer architecture

## What JMO Proved

- Dense documentation can be made queryable
- Expert corrections compound in value
- The pattern generalizes beyond a single domain

## Evolution

JMO evolved into CMMC-Buddy when the expert translation layer (Layer 2) was added — specifically the mapping of CMMC objectives to Microsoft Graph API calls.

The core architecture remained the same:
```
Layer 3: Corrections (AMP)     ← JMO had this
Layer 2: Expert Translation    ← CMMC-Buddy added this
Layer 1: Foundation Data       ← JMO had this
```

## Running JMO

JMO uses the same core gateway as CMMC-Buddy. The difference is in the data:

```bash
cd examples/jmo
python -m venv .venv
source .venv/bin/activate
pip install -r ../../requirements.txt

# Configure
export ANTHROPIC_API_KEY="your-key"

# Ingest your foundation data
python -m core.ingest.ingest_full

# Run
uvicorn core.gateway.main:app --port 8081
```

## Lesson Learned

JMO showed that Layer 1 (foundation data) + Layer 3 (corrections) creates a useful system. But the real value unlock came from Layer 2 (expert translation) — the "how to actually do it" that takes domain expertise to build.

That insight led to Praxis as a generalizable framework.
