# J-Mo — Mortgage Underwriting Compliance Assistant

J-Mo helps mortgage underwriters navigate lending guidelines, agency requirements, and compliance rules.

## Status: Ready to Run

### Layer 1 (Foundation) — Included
| Source | File | Size |
|--------|------|------|
| FHA Handbook 4000.1 | `data/pdfs/FHA_Handbook_4000.1.pdf` | 6.7MB |
| Freddie Mac Seller/Servicer Guide | `data/pdfs/Freddie_Mac_Seller_Servicer_Guide.pdf` | 31MB |
| USDA HB-1-3555 Guaranteed Loan | `data/pdfs/USDA_HB-1-3555_Guaranteed_Loan.pdf` | 6.8MB |

**After ingestion: 4,416 chunks** in ChromaDB

### Layer 1 (Foundation) — Still Needed
- ⏳ Fannie Mae Selling Guide
- ⏳ VA Lender's Handbook
- ⏳ TRID/TILA-RESPA requirements

### Layer 2 (Expert Translation) — Needed
The "what underwriters actually check" mappings:
- Common file deficiencies that cause suspensions
- Condition clearing requirements
- AUS findings interpretation (DU/LP)
- Income calculation methods by employment type

### Layer 3 (Corrections) — Ready
AMP/Nellie integration enabled. Corrections compound with real underwriting Q&A.

## Quick Start

```bash
cd examples/jmo
python -m venv .venv
source .venv/bin/activate
pip install -r ../../requirements.txt

# Configure
export ANTHROPIC_API_KEY="your-key"

# Ingest PDFs into ChromaDB (creates 4,416 chunks)
python extract_and_load.py

# Run
uvicorn gateway.main:app --port 8081
```

## Example Queries

- "What is the minimum borrower contribution for FHA?"
- "What is the maximum LTV for Freddie Mac cash-out refinance?"
- "Gift fund documentation requirements for conventional?"
- "How do I calculate rental income from a departing residence?"

## Architecture

Same three-layer Praxis pattern as CMMC-Buddy:
- **Layer 1**: PDF guidelines → section-based chunks → ChromaDB
- **Layer 2**: Expert translation (needed)
- **Layer 3**: AMP corrections (ready)

## License

Proprietary. Part of Praxis.
