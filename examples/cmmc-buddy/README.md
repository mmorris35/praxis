# CMMC-Buddy

A Praxis implementation for CMMC Level 2 compliance assessment.

## What's Included

### Foundation Data (Layer 1)
| Source | Controls | File |
|--------|----------|------|
| NIST 800-53 Rev 5 | 1,196 | `800-53-rev5.json` |
| NIST 800-171 Rev 3 | 130 | `800-171-rev3.json` |
| NIST CSF 2.0 | 219 | `csf-2.0.json` |
| FedRAMP HIGH | 410 | `fedramp-high.json` |
| **Total** | **1,955** | |

All data sourced from official NIST OSCAL repositories.

### Expert Translation (Layer 2)
| Source | Items | File |
|--------|-------|------|
| CMMC L2 Objectives | 320 | `cmmc-objectives-graph.json` |
| Graph API Endpoints | 55 | `graph-endpoints.json` |
| API References | 826 | (embedded in objectives) |
| 800-171→800-53 Mapping | 97 | `800-171-to-800-53-mapping.json` |

Each CMMC objective includes:
- What the assessor actually wants
- Microsoft Graph API calls with purpose
- Required manual documentation
- Common gaps organizations miss
- Assessor tips from real assessments

### Corrections (Layer 3)
Enabled via AMP/Nellie integration. Corrections accumulate with use.

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure
cp config/gateway.yaml.template config/gateway.yaml
# Edit gateway.yaml with your API keys

# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export NELLIE_URL="http://your-nellie-server:8765"

# Ingest data (requires Ollama with nomic-embed-text)
python -m ingest.ingest_full

# Run
uvicorn gateway.main:app --host 0.0.0.0 --port 8081
```

## Sample Queries

### Assessment & Evidence
- "How do I assess CMMC objective AC.L2-3.1.1-a?"
- "What Graph API calls do I need for access control assessment?"
- "What are common gaps for session termination controls?"

### Control Mapping
- "How does 800-171 control 3.1.1 map to 800-53?"
- "Which 800-171 controls address MFA?"

### Implementation
- "How do I implement session lock in Microsoft 365?"
- "What Conditional Access policies satisfy AC.L2-3.1.12?"

## Output Format

CMMC-Buddy provides ready-to-run commands in both formats:

### PowerShell (Microsoft Graph SDK)
```powershell
Connect-MgGraph -Scopes "User.Read.All","Directory.Read.All"
Get-MgUser -All -Property displayName,userPrincipalName,signInActivity | 
  Export-Csv -Path "UserInventory.csv"
```

### curl (REST API)
```bash
TOKEN=$(az account get-access-token --resource https://graph.microsoft.com --query accessToken -o tsv)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://graph.microsoft.com/v1.0/users?\$select=displayName,userPrincipalName" | jq
```

## Data Sources

### Official NIST OSCAL
- https://github.com/usnistgov/oscal-content
- NIST SP 800-53, 800-171, CSF

### FedRAMP
- https://github.com/GSA/fedramp-automation

### CMMC Assessment Mapping
- Proprietary expert mapping (Layer 2)
- Based on real assessment experience

## Architecture

See [Praxis Architecture](../../docs/architecture.md) for the full pattern.

## License

Proprietary. Part of Praxis.
