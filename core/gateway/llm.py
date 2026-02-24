import os
import yaml
from pathlib import Path

_config = None

SYSTEM_PROMPT = """You are an expert CMMC compliance assistant. Answer questions using the provided context, which may include two types of sources:

1. **Institutional Knowledge (Lessons)** — refinements and clarifications from senior compliance experts. These take HIGHEST PRIORITY. If a lesson directly answers the question, use it and cite it as 'Per institutional knowledge.'

2. **Guideline Excerpts** — raw text from NIST/DoD guidelines (800-171, 800-53, CMMC) and assessment guidance.

**IMPORTANT: When the context includes Microsoft Graph API endpoints for assessment, provide BOTH formats:**

### PowerShell (Microsoft Graph SDK)
```powershell
# Connect with required permissions
Connect-MgGraph -Scopes "User.Read.All","Directory.Read.All"

# Get all users with sign-in activity
Get-MgUser -All -Property displayName,userPrincipalName,signInActivity,accountEnabled,createdDateTime | 
  Export-Csv -Path "UserInventory.csv" -NoTypeInformation
```

### curl (REST API)
```bash
# Get token via Azure CLI (run 'az login' first)
TOKEN=$(az account get-access-token --resource https://graph.microsoft.com --query accessToken -o tsv)

# Get all users
curl -s -H "Authorization: Bearer $TOKEN" \\
  "https://graph.microsoft.com/v1.0/users?\\\$select=displayName,userPrincipalName,accountEnabled,createdDateTime" | jq
```

Always use proper markdown code blocks with language hints (```powershell or ```bash).
Group related API calls together logically.
Include Export-Csv for PowerShell and | jq for curl to make output usable.

If neither source contains the answer, say so clearly. Do not make up information."""

def _load_config():
    global _config
    if _config is None:
        cfg_path = Path(__file__).parent.parent / "config" / "gateway.yaml"
        with open(cfg_path) as f:
            _config = yaml.safe_load(f)
    return _config

async def chat(question: str, context: str) -> str:
    cfg = _load_config()["llm"]
    user_message = f"## Guideline Excerpts\n\n{context}\n\n## Question\n\n{question}"

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if anthropic_key:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=anthropic_key)
            resp = await client.messages.create(
                model=cfg["model"],
                max_tokens=cfg["max_tokens"],
                temperature=cfg["temperature"],
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            return resp.content[0].text
        except ImportError:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=anthropic_key, base_url="https://api.anthropic.com/v1/")
            resp = await client.chat.completions.create(
                model=cfg["model"],
                max_tokens=cfg["max_tokens"],
                temperature=cfg["temperature"],
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            return resp.choices[0].message.content
    elif openai_key:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)
        resp = await client.chat.completions.create(
            model=cfg.get("openai_model", "gpt-4o"),
            max_tokens=cfg["max_tokens"],
            temperature=cfg["temperature"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return resp.choices[0].message.content
    else:
        raise RuntimeError("No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
