# RealPraxis: Real Estate Sales Assistant

A Praxis implementation for residential real estate brokerages.

## The Problem

Real estate agents ask the same questions constantly:
- "What disclosures do I need for this property?"
- "Can the buyer back out now?"
- "How do I handle this multiple offer situation?"
- "What's our policy on dual agency?"

Managing brokers spend hours answering. Top producers hoard knowledge. New agents take months to get productive. When someone leaves, their expertise walks out the door.

## The Solution

An AI assistant that:
- Knows state regulations, MLS rules, and standard forms
- Knows your brokerage's policies and procedures
- Learns from your top producers' real-world experience
- Gets smarter every time someone uses it

---

## Layer 1: Foundation Data

### Federal
| Source | Description |
|--------|-------------|
| Fair Housing Act | Protected classes, prohibited practices |
| RESPA | Settlement procedures, disclosures |
| TILA / Reg Z | Loan advertising rules |
| Lead-Based Paint Disclosure | Pre-1978 homes |

### State (California example)
| Source | Description |
|--------|-------------|
| DRE Regulations | Licensing, agency, disclosure requirements |
| Civil Code §1102+ | Transfer Disclosure Statement (TDS) |
| Natural Hazard Disclosure | Flood, fire, earthquake zones |
| Mello-Roos / Special Tax | District disclosures |
| HOA Disclosures | CC&Rs, budget, litigation |

### MLS
| Source | Description |
|--------|-------------|
| MLS Rules & Regulations | Listing requirements, cooperation rules |
| IDX/VOW Policies | Online display rules |
| Lockbox Procedures | Access protocols |

### Forms (C.A.R. example)
| Form | Purpose |
|------|---------|
| RPA | Residential Purchase Agreement |
| AVID | Agent Visual Inspection Disclosure |
| TDS | Transfer Disclosure Statement |
| SPQ | Seller Property Questionnaire |
| SBSA | Statewide Buyer Seller Advisory |
| AD | Agency Disclosure |
| ... | 50+ additional forms |

---

## Layer 2: Institutional Knowledge

This is where it gets valuable. What your brokerage actually does:

### Policies & Procedures
- Commission structures and splits
- Transaction coordinator workflow
- Dual agency policy (beyond legal minimum)
- Team structures and responsibilities
- Escalation procedures

### Local Market Knowledge
- Typical earnest money amounts
- Common contingency timelines
- Who customarily pays for what (title, escrow, etc.)
- Local inspection norms
- Neighborhood-specific considerations

### Best Practices (from top producers)
- Multiple offer handling strategies
- Inspection negotiation tactics
- How to read a preliminary title report
- When to recommend specific inspections
- Red flags in disclosures
- How to price competitively

---

## Layer 3: Refinements

As agents use the system, they teach it:

### Example Refinements
- "Actually, in our market, buyers typically ask for 17-day inspection contingency, not 10"
- "For properties in [SUBDIVISION], always check for the CC&R amendment about solar panels"
- "When dealing with [LENDER], expect 45-day close minimum"
- "Our office policy is to always recommend sewer lateral inspection for pre-1980 homes"

---

## Example Queries

### Disclosures
> **Q:** "What disclosures are required for a 1965 home in a fire zone with an HOA?"
>
> **A:** Required disclosures:
> - Lead-Based Paint Disclosure (pre-1978)
> - Transfer Disclosure Statement (TDS)
> - Natural Hazard Disclosure (fire zone)
> - HOA documents (CC&Rs, budget, minutes, litigation)
> - Mello-Roos disclosure (if applicable)
>
> Forms needed: [LIST]
> Common mistakes: [LIST]

### Contingencies
> **Q:** "Buyer wants to cancel during inspection contingency. What's the process?"
>
> **A:** If within contingency period:
> 1. Buyer delivers Notice to Seller to Perform or Cancellation
> 2. Use form [CR] for cancellation
> 3. Earnest money release requires mutual agreement [form]
>
> Watch out for: Contingency removal deadlines, proper delivery method
>
> *Per brokerage policy: Always consult with [MANAGER] before advising on cancellation.*

### Agency
> **Q:** "Listing agent wants to also represent buyer. What do I need?"
>
> **A:** Dual agency in California requires:
> - Written consent from both parties (AD form)
> - Disclosure of limitations (can't advocate for either side on price)
> - Both parties sign acknowledgment
>
> *Brokerage policy: Dual agency requires broker approval. Submit request to [PROCESS].*

### Negotiations
> **Q:** "We have 5 offers on a listing. How should we handle this?"
>
> **A:** Multiple offer options:
> 1. Accept best offer
> 2. Counter one offer
> 3. Counter multiple offers (disclose to all)
> 4. Request highest and best from all
>
> *Per [TOP PRODUCER]: In this market, calling for highest-and-best with 24hr deadline typically yields 5-10% over asking. Make sure to disclose multiple offer situation to all parties.*

---

## Target Customer

### Ideal Profile
- **Size:** 20-200 agents (big enough to have pain, small enough to decide quickly)
- **Pain:** Managing broker overwhelmed with questions
- **Trigger:** Recent turnover of experienced agent, new agent class, compliance incident
- **Champion:** Managing broker, Director of Training, or COO

### Red Flags
- Tiny brokerage (1-5 agents) — not enough volume
- Mega-brokerage (1000+ agents) — too slow to decide
- No documented P&P — nothing to ingest
- "We just use ChatGPT" — need to show differentiation

---

## Implementation Notes

### Data Sources
- State real estate commission website (regs)
- MLS rules (usually PDF from MLS)
- Form library (C.A.R., local association)
- Brokerage P&P manual
- Training materials
- Top producer interviews (2-3 hours)

### Chunking Strategy
- One form = one chunk (with metadata: form number, purpose, when to use)
- Regulations by section
- P&P by topic
- Q&A pairs from training materials

### Integration Opportunities
- Transaction management system (Dotloop, SkySlope)
- CRM (Follow Up Boss, kvCORE)
- MLS (for property-specific context)

---

## Pricing Consideration

Real estate brokerages are cost-conscious. Consider:
- Per-agent pricing ($X/agent/month)
- Pilot at reduced rate to prove value
- ROI story: If managing broker saves 5 hrs/week = $X/year

---

## Competitive Landscape

| Competitor | What They Do | Gap |
|------------|--------------|-----|
| ChatGPT/Claude | General AI | No real estate knowledge, no learning |
| Lofty AI | Lead response | Not compliance/training focused |
| Inside Real Estate | CRM + websites | No expert system |
| Brokerage training platforms | Static content | Doesn't learn, not conversational |

**Our edge:** Learns from your top producers. Captures institutional knowledge. Gets smarter with use.

---

## Next Steps

1. [ ] Identify pilot brokerage (California ideal for first — most complex disclosures)
2. [ ] Obtain C.A.R. forms library
3. [ ] Get sample brokerage P&P manual
4. [ ] Interview 2-3 experienced agents for Layer 2
5. [ ] Build demo with California focus
