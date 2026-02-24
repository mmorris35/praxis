# CMMC Compliance Assistant
### Powered by Praxis

---

## The Problem

**300,000+ defense contractors need CMMC Level 2 certification.**

Your team is drowning in:
- 110 CMMC practices across 14 domains
- 800-171, 800-53, NIST CSF cross-references
- Assessment prep that takes months
- Questions that only your security expert can answer

**The cost:** Senior staff spend hours on questions. Junior staff wait for answers. Audits get delayed.

---

## The Solution

An AI compliance assistant that:

✅ **Knows the frameworks** — 1,955 controls from 800-53, 800-171, CSF, FedRAMP  
✅ **Knows what assessors want** — 320 objectives mapped to evidence collection  
✅ **Gives you the commands** — PowerShell and Graph API calls ready to run  
✅ **Learns from your team** — Every refinement makes it smarter  

---

## How It Works

```
Ask a question
    ↓
Get a practical answer with citations
    ↓
Not perfect? Click "Refine" and teach it
    ↓
Next time, it knows better
```

**Week 1:** Your expert teaches it 50 things → 85% accuracy  
**Month 1:** 200+ refinements → handles edge cases  
**Month 6:** Institutional knowledge that survives turnover  

---

## Example

**Question:** "How do I demonstrate AU.L2-3.3.1 for a Microsoft 365 environment?"

**Answer:**
> AU.L2-3.3.1 requires audit logging of user actions. For M365:
>
> **Evidence to collect:**
> - Unified Audit Log status
> - Audit retention policy (minimum 90 days for Level 2)
> - Sample audit log export
>
> **PowerShell:**
> ```powershell
> Get-AdminAuditLogConfig | Select-Object UnifiedAuditLogIngestionEnabled
> Get-UnifiedAuditLogRetentionPolicy
> ```
>
> **Common gaps:** UAL disabled by default, retention under 90 days, no log review process documented.

---

## Pricing

| Package | What You Get | Investment |
|---------|--------------|------------|
| **Pilot** | 4-week proof of concept, one domain focus | $10,000 |
| **Implementation** | Full CMMC L2 coverage, expert training, deployment | $45,000 |
| **Managed Service** | Hosting, LLM usage, support, updates | $3,000/mo |

*ROI: If your security lead spends 8 hours/week on compliance questions, that's $30K+/year in loaded cost.*

---

## Why Now?

- **CMMC 2.0 final rule:** Enforcement ramping up
- **C3PAO assessments:** Backlog means prep time is now
- **Institutional knowledge:** Capture it before your expert leaves

---

## Next Steps

1. **See the demo:** 15-minute call to see it in action
2. **Pilot:** 4-week proof of concept in your environment
3. **Deploy:** Full implementation with your team trained

---

**Contact:** [YOUR INFO]

*Powered by Praxis — Expert systems that learn*
