# J-Mo — Mortgage Underwriting Compliance Assistant

J-Mo helps mortgage underwriters navigate lending guidelines, agency requirements, and compliance rules.

## Status: Foundation Data Included

### Layer 1 (Foundation) — Included
- ✅ **FHA Handbook 4000.1** (6.7MB) — `data/pdfs/FHA_Handbook_4000.1.pdf`
- ✅ **Freddie Mac Seller/Servicer Guide** (31MB) — `data/pdfs/Freddie_Mac_Seller_Servicer_Guide.pdf`
- ✅ **USDA HB-1-3555 Guaranteed Loan** (6.8MB) — `data/pdfs/USDA_HB-1-3555_Guaranteed_Loan.pdf`

### Layer 1 (Foundation) — Still Needed
- ⏳ **Fannie Mae Selling Guide**
- ⏳ **VA Lender's Handbook**
- ⏳ **TRID/TILA-RESPA requirements**
- ⏳ **State-specific lending regulations**
- ⏳ **Investor overlays** (org-specific)

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
