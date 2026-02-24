# RealPraxis: Bay Area Real Estate Assistant

A Praxis implementation for San Francisco Bay Area residential real estate brokerages.

## Why the Bay Area?

The Bay Area is **the hardest real estate market in America** to practice in:
- City-specific disclosure requirements (SF, Oakland, Berkeley all different)
- Rent control in multiple jurisdictions with different rules
- Point-of-sale ordinances that vary by city
- TIC properties, ADUs, soft-story retrofits
- $1M+ price points where mistakes are expensive
- Hyper-competitive market dynamics (multiple offers, waived contingencies)

**If it works here, it works anywhere.**

---

## The Problem

Bay Area agents face unique complexity:
- "What disclosures do I need for this Oakland duplex?"
- "Is this SF property subject to soft-story retrofit?"
- "Can my buyer waive the inspection contingency? Should they?"
- "This Berkeley property has a rental unit — what am I required to disclose?"
- "What's the 3R report and when do I need it?"

Managing brokers spend hours on these questions. Top producers know the answers but hoard the knowledge. New agents drown.

---

## Layer 1: Foundation Data

### Federal
| Source | Description |
|--------|-------------|
| Fair Housing Act | Protected classes, prohibited practices |
| RESPA | Settlement procedures, kickback rules |
| Lead-Based Paint Disclosure | Pre-1978 homes (most Bay Area housing) |

### California State
| Source | Description |
|--------|-------------|
| DRE Regulations | Licensing, agency, broker supervision |
| Civil Code §1102+ | Transfer Disclosure Statement (TDS) |
| Natural Hazard Disclosure (NHD) | Flood, fire, earthquake, environmental |
| Mello-Roos / Special Tax | District disclosures |
| HOA Disclosures (Civil Code §4525) | Budget, reserves, litigation, CC&Rs |
| AB 968 (2019) | Fire hardening disclosures |
| SB 1079 (2020) | Foreclosure protections |

### Bay Area Local Associations
| Association | Coverage |
|-------------|----------|
| **SFAR** (SF Association of Realtors) | San Francisco |
| **CCAR** (Contra Costa AOR) | Contra Costa County |
| **BRIDGEMLS** | East Bay, Tri-Valley |
| **SAMCAR** (San Mateo County AOR) | Peninsula |
| **SILVAR** (Santa Clara County) | South Bay |
| **BAREIS** | North Bay (Marin, Sonoma, Napa) |

Each has supplemental forms and local rules beyond C.A.R.

### C.A.R. Forms (Core)
| Form | Purpose |
|------|---------|
| RPA-CA | Residential Purchase Agreement |
| PRDS | Purchase agreement (Peninsula/South Bay variant) |
| TDS | Transfer Disclosure Statement |
| SPQ | Seller Property Questionnaire |
| AVID | Agent Visual Inspection Disclosure |
| NHD | Natural Hazard Disclosure |
| FLD | Flood zone disclosure |
| SBSA | Statewide Buyer Seller Advisory |
| AD | Agency Disclosure |
| WCMD | Water Conserving Fixtures Compliance |
| SSD | Smoke/CO Detector Compliance |

---

## City-Specific Requirements (The Hard Part)

### San Francisco
| Requirement | Details |
|-------------|---------|
| **3R Report** | Required disclosure of permits, zoning, code violations |
| **Sewer Lateral Ordinance** | Compliance required at sale for most properties |
| **Soft-Story Retrofit** | Wood-frame buildings 3+ stories, 5+ units |
| **Rent Ordinance** | Rent control, just cause eviction, buyout disclosures |
| **Condo Conversion** | Lottery, tenant protections |
| **Ellis Act** | Specific rules for removing rental units |
| **Energy/Water Conservation** | Point-of-sale compliance |
| **Residential Rent Stabilization** | Applies to most buildings pre-1979 |
| **ADU Regulations** | Specific SF rules beyond state |

### Oakland
| Requirement | Details |
|-------------|---------|
| **Soft-Story Retrofit** | Mandatory for qualifying buildings |
| **Rent Adjustment Program** | Rent control for pre-1983 buildings |
| **Just Cause for Eviction** | Required disclosures |
| **Tenant Protection Ordinance** | Enhanced protections |
| **Sewer Lateral** | Compliance may be required |
| **Point-of-Sale Energy** | Depends on property type |

### Berkeley
| Requirement | Details |
|-------------|---------|
| **Rent Stabilization Board** | Strict rent control |
| **Inspection Requirement** | Pre-sale inspection for some properties |
| **Smoke Detector Hardwire** | Point-of-sale requirement |
| **Sewer Lateral** | Compliance at sale |
| **Energy Audit** | RECO compliance |

### Other Bay Area Cities
| City | Notable Requirements |
|------|---------------------|
| **San Jose** | Rent control (AB 1482), apartment rent ordinance |
| **Mountain View** | CSFRA rent control |
| **East Palo Alto** | Strict rent control |
| **Richmond** | Rent control |
| **Alameda** | Rent control for some units |
| **Hayward** | Rent control |
| **Fremont** | Mobile home rent control |

---

## Layer 2: Bay Area Institutional Knowledge

### Market Dynamics
- **Multiple offers are normal** — strategy matters
- **Waived contingencies** — when appropriate vs. reckless
- **Pre-listing inspections** — common practice, seller provides
- **As-is sales** — understanding what this really means
- **Appraisal gaps** — how to handle in competitive situations
- **Backup offers** — when and how to structure

### Local Customs
| Custom | Bay Area Norm |
|--------|---------------|
| Earnest money | 3% typical, higher for competitive offers |
| Inspection contingency | 7-10 days (sometimes 0 in hot markets) |
| Loan contingency | 17-21 days |
| Close of escrow | 30 days typical, 21 for competitive |
| Who pays title | Varies by county (split common) |
| Who pays transfer tax | City-specific (SF = seller, some cities = split) |
| Pre-inspections | Seller commonly provides reports upfront |

### Property Types (Bay Area Specific)
| Type | Complexity |
|------|------------|
| **TIC (Tenancy in Common)** | SF specialty — financing, insurance, conversion rights |
| **Condo** | HOA diligence, litigation history |
| **2-4 Units** | Rent control analysis, income verification |
| **SFR with ADU** | Permit status, rental income, compliance |
| **Soft-Story Building** | Retrofit status, cost, compliance deadline |
| **Historic/Mills Act** | Tax benefits, restrictions |

### Lender Knowledge
- **Local lenders** who know Bay Area quirks (TIC financing, etc.)
- **Typical timelines** by lender
- **Which lenders** handle tricky property types
- **Appraisal issues** common in the market

---

## Layer 3: Refinements (Examples)

What Bay Area agents would teach the system:

> "For any property in SF built before 1979, always verify rent control status even if owner-occupied — the unit may have protected tenants if ever rented."

> "In Oakland, soft-story retrofit compliance is on the seller, but get written verification — some owners claim compliance but never filed."

> "When a Berkeley buyer asks about the property's rental history, remember RECO requires energy audit compliance at sale."

> "For TICs in SF, always verify the TIC agreement allows refinancing — some old agreements restrict it."

> "In multiple offer situations in this market, love letters don't work anymore and create Fair Housing risk. Focus on terms, not feelings."

> "3R reports in SF can take 3-4 weeks right now. If listing in SF, order it immediately."

---

## Example Queries

### City-Specific Compliance
> **Q:** "I'm listing a 1960s duplex in Oakland with a long-term tenant. What do I need?"
>
> **A:** For an Oakland duplex (pre-1983):
> 
> **Rent Control:**
> - Property is covered by Oakland Rent Adjustment Program
> - Provide tenant with required disclosures
> - Verify current rent is at or below allowed limit
> - Buyer must honor existing lease and rent control
>
> **Point of Sale:**
> - Check soft-story retrofit status (mandatory for 2+ story, 2+ units)
> - Sewer lateral compliance may be required
> 
> **Disclosures:**
> - TDS, NHD, lead-based paint (pre-1978)
> - Rent stabilization disclosure to buyer
> - Just Cause eviction requirements
>
> **Forms:** [LIST]
>
> ⚠️ *Recommend: Consult with Oakland rent board before listing. Verify retrofit status with city.*

### TIC Properties
> **Q:** "Buyer wants to purchase a 2-unit TIC in SF. What should I tell them about financing?"
>
> **A:** TIC financing in SF:
>
> **Financing Options:**
> - Fractional/TIC loans (specialty lenders: Sterling, Patelco, First Republic legacy)
> - Higher rates than condo (typically 0.5-1% premium)
> - Larger down payment often required (20-25%)
>
> **TIC Agreement Review:**
> - Verify refinancing rights
> - Check sale approval process
> - Understand expense sharing
> - Review buyout provisions
>
> **Condo Conversion:**
> - Check lottery status / eligibility
> - Bypass eligibility if 6+ years ownership
>
> *Per [TOP PRODUCER]: Always recommend TIC attorney review before removing contingencies. Agreement terms vary wildly and can affect resale.*

### Multiple Offers
> **Q:** "My listing has 12 offers. How do I handle this?"
>
> **A:** With 12 offers in this market:
>
> **Options:**
> 1. Review all, accept best overall (terms + price + certainty)
> 2. Call for highest and best (set deadline, 24-48 hrs)
> 3. Counter top 2-3 with specific terms
>
> **Evaluation Criteria:**
> - Price (but not everything)
> - Down payment percentage (more = more certainty)
> - Contingency waiver/shortening
> - Loan pre-approval strength (local lender vs. online)
> - Close of escrow timeline
> - Appraisal gap coverage
>
> **Required Disclosures:**
> - Must disclose existence of multiple offers if asked
> - Must present all offers to seller
> - No cherry-picking or hiding offers
>
> *Bay Area norm: Pre-inspection by seller + short contingencies + strong pre-approval typically wins over highest price with weak terms.*

---

## Target Customer: Bay Area Brokerages

### Ideal Profile
| Criteria | Target |
|----------|--------|
| Size | 25-150 agents |
| Markets | SF, Peninsula, East Bay, South Bay |
| Pain | Agents asking city-specific questions constantly |
| Champion | Managing broker, Director of Training |
| Trigger | New agents drowning, compliance scare, key agent left |

### Named Targets (Research Needed)
- **Compass** (local offices)
- **Coldwell Banker** (Bay Area offices)
- **Intero**
- **Sereno**
- **Vanguard Properties**
- **Zephyr Real Estate**
- **Red Oak Realty**
- **Keller Williams** (Bay Area offices)
- **Independent brokerages** (50-100 agents)

---

## Data Sources to Acquire

### Must Have
- [ ] C.A.R. forms library (member access)
- [ ] SFAR supplemental forms
- [ ] SF 3R report requirements + sample
- [ ] SF Rent Ordinance summary
- [ ] Oakland Rent Adjustment Program rules
- [ ] Berkeley rent control guide
- [ ] Soft-story retrofit requirements (SF, Oakland)
- [ ] Sewer lateral ordinances by city
- [ ] NHD report sample and interpretation guide

### Nice to Have
- [ ] Sample brokerage P&P manual
- [ ] MLS rules (SFARMLS, BRIDGEMLS)
- [ ] Title company local customs guide
- [ ] Escrow timeline guides
- [ ] Lender comparison (TIC, jumbo, etc.)

---

## Implementation Plan

### Phase 1: SF Focus (Week 1-4)
- Ingest C.A.R. forms
- Ingest SF-specific requirements (3R, rent control, sewer, soft-story)
- Build basic Q&A capability
- Test with SF-specific queries

### Phase 2: Expand to East Bay (Week 5-6)
- Add Oakland, Berkeley requirements
- Add rent control variations
- Test with multi-city queries

### Phase 3: Full Bay Area (Week 7-8)
- Add Peninsula, South Bay, North Bay
- Add county-specific customs
- Layer 2: Top producer interviews
- Launch pilot

---

## Competitive Advantage

**No one else has this.**

Generic AI doesn't know:
- When you need a 3R report
- Which cities have soft-story requirements
- How TIC financing works
- That Berkeley requires pre-sale inspection for some properties
- What "Oakland rent control" actually means for a sale

**We will.**

And we'll get smarter every time a Bay Area agent teaches us something new.

---

## Next Steps

1. [ ] Connect with Bay Area brokerage contact
2. [ ] Acquire C.A.R. forms library access
3. [ ] Download SF, Oakland, Berkeley city requirements
4. [ ] Build Layer 1 ingest pipeline
5. [ ] Identify 2-3 top producers for Layer 2 interviews
6. [ ] Launch SF-only demo
