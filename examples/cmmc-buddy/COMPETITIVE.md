# JMO — Competitive Landscape

## Friday Harbor (fridayharbor.ai)

### What They Are
AI Mortgage Originator Assistant. Multi-agent system that automates loan file assembly and pre-underwriting.

- **Backed by:** Allen Institute for AI (AI2, founded by Paul Allen), $6M seed round (April 2025)
- **Traction:** ~25 lenders, including 2 top-10 independent mortgage banks
- **Tech stack:** LangChain, GPT, multi-agent framework (built by Nomtek)
- **Integrations:** Encompass LOS (ICE Mortgage Technology), Fannie Mae Income Calculator
- **Recognition:** HousingWire 2026 Tech100 Mortgage list

### What They Do
1. **Document OCR & Analysis** — reads W-2s, bank statements, tax returns, appraisals
2. **Automated Pre-Underwriting** — checks borrower data against agency guidelines, flags issues in real-time
3. **Dynamic Checklist** — guides loan officers through document collection
4. **Scenario Desk** — structures deals and answers guideline questions
5. **LOS Integration** — loan files update automatically in Encompass
6. **Appraisal Review** — AI review of appraisal files and photos against Fannie/Freddie guidelines
7. **Lender/Investor Overlays** — applies company-specific rules on top of agency guidelines

### Where They Win
- **Process automation** — they replace manual file review, not just answer questions
- **LOS integration** — plugs into the existing mortgage tech stack
- **Document intelligence** — reads actual borrower documents, not just guidelines
- **Enterprise sales motion** — already selling to top-10 lenders
- **Funding & credibility** — AI2 backing, HousingWire recognition

### Where They Don't Compete With JMO

| Capability | Friday Harbor | JMO |
|-----------|--------------|-----|
| Read borrower documents | ✅ Core feature | ❌ Not the use case |
| Automated pre-underwriting | ✅ Core feature | ❌ Not the use case |
| LOS integration | ✅ Encompass | ❌ Standalone |
| Guideline Q&A | ⚠️ Scenario Desk (static) | ✅ Core feature |
| Learning from corrections | ❌ No evidence | ✅ AMP — core differentiator |
| Institutional knowledge capture | ❌ No evidence | ✅ Lessons persist forever |
| Company overlay learning | ⚠️ Pre-configured | ✅ Learned from expert corrections |
| Domain-agnostic | ❌ Mortgage only | ✅ Any regulatory domain |
| Expert knowledge retention | ❌ Knowledge walks when expert leaves | ✅ Knowledge stays in AMP |

### The Key Distinction

**Friday Harbor automates the process.** It's a workflow tool that replaces manual file review and document checking. It answers "is this loan file complete and compliant?"

**JMO captures the expertise.** It's a knowledge tool that replaces asking the senior person. It answers "what does the guideline say about X, considering our company's interpretation?"

They solve different problems for different buyers:
- **Friday Harbor buyer:** VP of Operations, COO — wants to scale processing capacity without hiring
- **JMO buyer:** Underwriting manager, training director — wants to stop answering the same question 50 times and preserve institutional knowledge

### Competitive Risk

Friday Harbor's "Scenario Desk" feature is the closest overlap — it "structures deals and answers questions with knowledge of the guidelines." If they add a feedback/correction loop (learning from underwriter corrections), they'd drift into JMO's lane.

**However:**
- Their architecture is multi-agent workflow, not knowledge management
- Adding AMP-style learning would be a significant pivot in their architecture
- Their go-to-market is enterprise sales to lenders — different motion than knowledge capture
- They're mortgage-only; JMO's value prop is domain-agnostic

### Complementary Play

A mortgage shop could realistically use **both**:
- Friday Harbor for loan file assembly and automated pre-underwriting
- JMO for guideline Q&A, training new underwriters, and capturing institutional knowledge

They don't replace each other. Friday Harbor is the assembly line. JMO is the expert sitting next to you.

---

## Other Players to Watch

### Aklimate (aklimate.ai)
- AI underwriting assistant
- Focus on income calculation automation
- Smaller scale than Friday Harbor

### Capacity (capacity.com)
- AI-powered support automation platform
- Not mortgage-specific but used in financial services
- Knowledge base + helpdesk, no learning loop

### Vesta (vestaai.com)
- AI for mortgage document processing
- Focus on data extraction from loan docs
- Similar to Friday Harbor's OCR layer

### Generic RAG Tools (Glean, Guru, etc.)
- Enterprise search/knowledge tools
- Can ingest mortgage guidelines
- No domain expertise, no correction loop, no AMP
- JMO without the learning = these tools

---

## JMO's Defensible Position

1. **AMP is architecturally unique.** No competitor has a correction-to-lesson feedback loop that compounds over time.
2. **Domain-agnostic.** Friday Harbor is locked into mortgage. JMO works anywhere there are dense guidelines and tired experts.
3. **The moat deepens with use.** 6 months of corrections can't be replicated by uploading PDFs. That's institutional knowledge, not data.
4. **Open architecture.** AMP protocol means any memory server slots in — not locked to one vendor.
5. **Low barrier to entry.** Upload PDFs → get answers in minutes. No LOS integration required. No enterprise sales cycle for initial adoption.

---

*Last updated: 2026-02-17*
*Add new competitors as discovered.*
