# J-Mo — Mortgage Underwriting Compliance Assistant

J-Mo helps mortgage underwriters navigate lending guidelines, agency requirements, and compliance rules.

## Status: Needs Foundation Data

### Layer 1 (Foundation) — Data Needed
- **Fannie Mae Selling Guide**
- **Freddie Mac Seller/Servicer Guide**
- **FHA Single Family Housing Policy Handbook (HUD 4000.1)**
- **VA Lender's Handbook**
- **USDA Rural Development Guidelines**
- **TRID/TILA-RESPA requirements**
- **State-specific lending regulations**
- **Investor overlays** (org-specific)

### Layer 2 (Expert Translation) — Needed
- What do underwriters actually check on each loan type?
- Common file deficiencies that cause suspensions
- Condition clearing requirements
- AUS findings interpretation (DU/LP)
- Income calculation methods by employment type
- Asset documentation requirements
- Credit exception guidelines
- Compensating factors that work

### Layer 3 (Corrections) — Ready
- AMP/Nellie integration enabled
- Corrections compound with real underwriting Q&A

## Example Queries (Once Built)

### Guideline Lookup
- "What are Fannie Mae's DTI limits for a conforming loan?"
- "What's the minimum credit score for FHA?"
- "Gift fund documentation requirements for conventional?"

### Underwriting Scenarios
- "Self-employed borrower with 1 year tax returns — options?"
- "How do I calculate rental income from a departing residence?"
- "Non-occupant co-borrower on FHA — allowed?"

### Condition Clearing
- "What clears a large deposit condition?"
- "Verbal VOE requirements for closing?"
- "How to document gap in employment?"

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: Corrections (AMP)              ✅ READY       │
│  └─ Real underwriter Q&A improves answers               │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: Expert Translation             ⏳ NEEDED      │
│  └─ What underwriters actually check                    │
│     - Common suspension reasons                         │
│     - Condition clearing patterns                       │
│     - AUS interpretation                                │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: Foundation Data                ⏳ NEEDED      │
│  └─ Agency guidelines (FNMA, FHLMC, FHA, VA)            │
│     - Investor overlays                                 │
│     - State regulations                                 │
└─────────────────────────────────────────────────────────┘
```

## Data Sources to Acquire

| Source | Format | Notes |
|--------|--------|-------|
| Fannie Mae Selling Guide | HTML/PDF | AllRegs or direct |
| Freddie Mac Guide | HTML/PDF | AllRegs or direct |
| HUD 4000.1 | PDF | hudclips.org |
| VA Lender's Handbook | PDF | VA.gov |
| USDA Guidelines | PDF | USDA RD |

## Running J-Mo

```bash
cd examples/jmo
python -m venv .venv
source .venv/bin/activate
pip install -r ../../requirements.txt

# Add guideline data to data/structured/
# Create ingest script for mortgage guidelines

export ANTHROPIC_API_KEY="your-key"
uvicorn core.gateway.main:app --port 8081
```

## Why This Matters

Mortgage underwriting has the same problem as CMMC:
- **Dense documentation** — thousands of pages across multiple agencies
- **Expert knowledge required** — guidelines don't tell you what actually works
- **Edge cases everywhere** — real loans don't match textbook scenarios

The Praxis pattern fits perfectly.

## License

Proprietary. Part of Praxis.
