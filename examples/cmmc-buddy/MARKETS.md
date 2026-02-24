# JMO — Market Opportunities

> Anywhere there's a mountain of dense regulatory text and a senior person tired of answering "what does the guideline say?" — that's the market.

## The Pattern

Every market below shares the same structure:

1. **Dense source docs** nobody wants to read
2. **A senior person** who knows where to find answers
3. **Junior people** who keep asking instead of looking
4. **The senior person's time** is expensive and their patience is finite
5. **Corrections compound** — AMP means the system gets smarter every time someone teaches it

---

## Tier 1 — Immediate Fit (same structure as mortgage)

### Mortgage Underwriting ← *Current demo*
- **Sources:** FHA Handbook 4000.1, Freddie Mac Guide, USDA HB-1-3555, VA Lender's Handbook, Fannie Mae Selling Guide, company overlays, investor guidelines
- **The tired expert:** Underwriting manager
- **The repeat question:** "What does the guideline say about [X]?"
- **AMP value:** Manager teaches it once, 50 underwriters stop asking
- **Complexity multiplier:** Agency guidelines + company overlays + investor requirements = three layers of rules for every question

### Tax Preparation
- **Sources:** IRS publications (Pub 17, Pub 535, Pub 946, etc.), IRC sections, state tax codes, firm-specific procedures, IRS notices and revenue rulings
- **The tired expert:** Senior tax preparer / tax partner
- **The repeat question:** "Can my client deduct this?" / "What form do I use for this?"
- **AMP value:** Partner teaches it once per tax season edge case, entire firm benefits
- **Scale:** ~500 IRS publications, 50 state tax codes, annual updates every January
- **Seasonal pain:** Tax season concentrates 80% of questions into 4 months

### Insurance Underwriting
- **Sources:** State insurance regulations, carrier guidelines, company rating manuals, ISO forms, NAIC model laws
- **The tired expert:** Senior underwriter / underwriting manager
- **The repeat question:** "What's our appetite for this risk?" / "Does this need a surcharge in [state]?"
- **AMP value:** Institutional knowledge about risk appetite is the hardest thing to document — AMP captures it naturally
- **Complexity multiplier:** 50 states × multiple carriers × product lines

### Legal Compliance (HIPAA, SOX, AML/KYC)
- **Sources:** Federal regulations (CFR titles), agency guidance letters, enforcement actions, firm compliance manuals
- **The tired expert:** Chief Compliance Officer / compliance team lead
- **The repeat question:** "Do we need to file an SAR for this?" / "Is this a HIPAA violation?"
- **AMP value:** Compliance decisions are high-stakes — having a verified, corrected knowledge base reduces risk
- **Scale:** Regulated industries spend $10K–$50K/employee on compliance annually

---

## Tier 2 — High Value, Jurisdiction-Dependent

### Building Codes & Inspections
- **Sources:** IRC (International Residential Code), IBC (International Building Code), local amendments, state-specific adoptions
- **The tired expert:** Chief building inspector / senior plan reviewer
- **The repeat question:** "What's the setback requirement?" / "Is this egress-compliant?"
- **AMP value:** Local amendments are the killer — every jurisdiction modifies the base code differently. AMP captures those local interpretations.
- **Complexity multiplier:** Base code × state adoption × local amendments × year of adoption. Same question, different answer by zip code.
- **Zip code angle:** Filter by jurisdiction automatically. "What's the minimum stair width?" depends entirely on where you are.

### City Permits & Zoning
- **Sources:** Municipal zoning codes, comprehensive plans, conditional use regulations, subdivision ordinances, historic district guidelines
- **The tired expert:** Planning director / senior planner
- **The repeat question:** "Can I build [X] on this lot?" / "Do I need a variance?"
- **AMP value:** Planners make interpretive decisions constantly — "we typically allow this" vs "we don't." AMP captures institutional practice, not just code text.
- **Scale:** 19,000+ municipalities in the US, each with unique zoning codes

### HOA / CC&Rs
- **Sources:** CC&Rs, architectural guidelines, board meeting minutes/precedents, state HOA statutes
- **The tired expert:** Property manager / HOA board president
- **The repeat question:** "Can I paint my house this color?" / "Can I build a fence?"
- **AMP value:** Board precedent matters. "We approved a similar request in 2022" is exactly the kind of institutional memory AMP captures.
- **Scale:** 370,000+ HOAs in the US, each with unique CC&Rs
- **Low-hanging fruit:** Property management companies managing 50+ communities — same platform, different docs per community

---

## Tier 3 — Large Enterprise / Government

### Government Contracting (FAR/DFARS)
- **Sources:** Federal Acquisition Regulation (FAR), Defense FAR Supplement (DFARS), agency-specific supplements, contract clauses
- **The tired expert:** Contracts manager / procurement officer
- **The repeat question:** "What's the small business set-aside threshold?" / "Which clause applies to this contract type?"
- **AMP value:** Acquisition is tribal knowledge — experienced COs know which clauses matter and which are boilerplate. AMP externalizes that.
- **Scale:** $700B+ in annual federal procurement

### Pharma / FDA Regulatory
- **Sources:** 21 CFR, FDA guidance documents, ICH guidelines, USP standards, company SOPs
- **The tired expert:** Regulatory affairs director
- **The repeat question:** "What clinical data do we need for a 510(k)?" / "What's the CMC requirement for this filing?"
- **AMP value:** FDA guidance is notoriously ambiguous. Institutional knowledge about "what the FDA actually expects" vs "what the guidance literally says" is the real value.
- **Scale:** Average drug approval costs $2.6B — even small efficiency gains are worth millions

### Healthcare / Clinical Guidelines
- **Sources:** Clinical practice guidelines (AHA, ACS, USPSTF), CMS coverage determinations, payer-specific policies, Lexicomp/UpToDate
- **The tired expert:** Medical director / utilization review nurse
- **The repeat question:** "Is this procedure medically necessary?" / "What's the prior auth requirement?"
- **AMP value:** Payer-specific variations on top of clinical guidelines — same pattern as mortgage (agency + company overlay + investor)
- **Overlap with Boredom Engine:** Failed treatments, adverse events, negative clinical evidence

---

## Tier 4 — Emerging / Niche

### Real Estate Transactions
- **Sources:** State-specific real estate laws, title standards, RESPA, TRID, agency-specific closing requirements
- **The tired expert:** Closing attorney / senior title officer
- **The repeat question:** "What documents do we need for closing in [state]?"

### Education / Accreditation
- **Sources:** Accreditation standards (SACSCOC, HLC, etc.), state education codes, Title IV regulations
- **The tired expert:** Institutional effectiveness director
- **The repeat question:** "Does this program change require a substantive change prospectus?"

### Environmental Compliance
- **Sources:** NEPA, CERCLA, state environmental regs, EPA guidance, EIS requirements
- **The tired expert:** Environmental compliance officer
- **The repeat question:** "Do we need a Phase II for this site?" / "What triggers an EIS?"

### Import/Export & Customs
- **Sources:** Harmonized Tariff Schedule, EAR, ITAR, customs rulings, free trade agreement rules of origin
- **The tired expert:** Trade compliance manager
- **The repeat question:** "What's the duty rate for this?" / "Do we need an export license?"

### Motorsport / Racing Regulations
- **Sources:** FIA Technical Regulations, series-specific rule books (F1, IndyCar, NASCAR), homologation docs
- **The tired expert:** Technical director / chief engineer
- **The repeat question:** "Is this modification legal under the current regs?"
- **AMP value:** Regulations change every season. Institutional knowledge about scrutineering interpretations is gold.

---

## The Moat

RAG chatbots are commodity. Everyone can chunk PDFs and point an LLM at them.

**AMP is the moat.** The correction loop means:
- Day 1: Generic RAG, ~60% accuracy
- Week 1: Senior expert teaches it 50 corrections, ~85% accuracy
- Month 1: 200+ corrections, handles edge cases, knows institutional interpretations
- Month 6: It basically *is* that senior expert's brain, available 24/7

You can't replicate 6 months of accumulated institutional knowledge by re-chunking PDFs. That's the lock-in. That's the product.

## Pricing Thoughts

- **Per-seat SaaS:** $50-200/user/month (depending on industry margin)
- **Enterprise:** $5K-50K/month per organization
- **Usage-based:** Per-question pricing for high-value verticals (legal, pharma)
- **Free tier → paid corrections:** Let anyone RAG their docs for free. Charge for AMP (the learning layer). Free gets you 60% accuracy. Paid gets you 95%.

---

*This document is alive. Add markets as we discover them.*
