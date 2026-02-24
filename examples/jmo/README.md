# JMO — Corporate & Investor Compliance Assistant

JMO (Just My Opinion) helps organizations navigate corporate governance, investor requirements, and proprietary compliance guidelines.

## Status: Foundation Ready, Expert Layer Needed

### Current State
- ✅ Core Praxis architecture working
- ✅ AMP corrections enabled
- ⏳ **Layer 1 (Foundation)**: Needs corporate/investor guideline documents
- ⏳ **Layer 2 (Expert Translation)**: Needs "what investors actually want" mapping

### Data Needed (Layer 1)
- Corporate governance frameworks
- Investor due diligence checklists
- Board reporting requirements
- Proprietary compliance guidelines (org-specific)
- SEC/regulatory disclosure requirements
- ESG reporting standards

### Expert Translation Needed (Layer 2)
- What do investors actually look for during due diligence?
- What are common governance gaps that kill deals?
- How do you prepare for board presentations?
- What evidence satisfies investor requirements?
- Red flags that sophisticated investors catch

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: Corrections (AMP)              ✅ READY       │
│  └─ Self-improving via real-world use                   │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: Expert Translation             ⏳ NEEDED      │
│  └─ "What investors actually want" mappings             │
│     - Due diligence expectations                        │
│     - Board presentation requirements                   │
│     - Common gaps that kill deals                       │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: Foundation Data                ⏳ NEEDED      │
│  └─ Corporate governance frameworks                     │
│     - Investor guidelines                               │
│     - Proprietary org-specific policies                 │
└─────────────────────────────────────────────────────────┘
```

## Running JMO

```bash
cd examples/jmo
python -m venv .venv
source .venv/bin/activate
pip install -r ../../requirements.txt

# Configure
export ANTHROPIC_API_KEY="your-key"

# Add your foundation data to data/structured/
# Then create an ingest script for your data format

# Run
uvicorn core.gateway.main:app --port 8081
```

## Comparison with CMMC-Buddy

| Aspect | CMMC-Buddy | JMO |
|--------|------------|-----|
| Domain | CMMC/NIST compliance | Corporate/investor compliance |
| Layer 1 | OSCAL frameworks (public) | Corporate guidelines (often proprietary) |
| Layer 2 | Graph API mappings (built) | Investor expectations (needed) |
| Layer 3 | AMP corrections | AMP corrections |
| Status | Production-ready | Foundation needed |

## Contributing Layer 2

If you have expertise in:
- Investor relations
- Corporate governance
- Due diligence processes
- Board operations

...the expert translation layer needs your knowledge. The pattern is the same as CMMC-Buddy:
1. What does the audience (investors/board) actually want?
2. What specific evidence satisfies them?
3. What are common gaps that cause problems?
4. What are the insider tips from experience?

## License

Proprietary. Part of Praxis.
