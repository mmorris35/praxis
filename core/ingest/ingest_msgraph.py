#!/usr/bin/env python3
"""Ingest MS Graph API and PowerShell reference docs into Praxis ChromaDB.

Fetches key reference pages from Microsoft's learn.microsoft.com,
parses markdown preserving code blocks and parameter tables,
and indexes into a 'msgraph-docs' ChromaDB collection.
"""
import re
import json
import hashlib
import requests
import chromadb
from pathlib import Path

# Import the same embedding function used by the rest of Praxis
from core.gateway.rag import LocalEmbeddingFunction

DATA_DIR = Path(__file__).parent.parent / "data"
MSGRAPH_DIR = DATA_DIR / "msgraph"
CHROMA_DIR = DATA_DIR / "chroma"

# Key MS Graph API docs to fetch from learn.microsoft.com
# Format: (slug, url_path, category, title)
GRAPH_API_DOCS = [
    # Users
    ("user-list", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/user-list.md", "Users API", "List users"),
    ("user-get", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/user-get.md", "Users API", "Get user"),
    ("user-create", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/user-post-users.md", "Users API", "Create user"),
    ("user-update", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/user-update.md", "Users API", "Update user"),
    ("user-delete", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/user-delete.md", "Users API", "Delete user"),
    # Groups
    ("group-list", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/group-list.md", "Groups API", "List groups"),
    ("group-get", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/group-get.md", "Groups API", "Get group"),
    ("group-create", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/group-post-groups.md", "Groups API", "Create group"),
    ("group-members-list", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/group-list-members.md", "Groups API", "List group members"),
    ("group-member-add", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/group-post-members.md", "Groups API", "Add group member"),
    # Mail
    ("message-list", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/user-list-messages.md", "Mail API", "List messages"),
    ("message-get", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/message-get.md", "Mail API", "Get message"),
    ("message-send", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/user-sendmail.md", "Mail API", "Send mail"),
    # Resources / types
    ("user-resource", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/resources/user.md", "Resources", "User resource type"),
    ("group-resource", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/resources/group.md", "Resources", "Group resource type"),
    # OData / query params
    ("query-parameters", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/concepts/query-parameters.md", "Query Parameters", "OData query parameters"),
    ("filter-query", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/concepts/filter-query-parameter.md", "Query Parameters", "$filter query parameter"),
    ("paging", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/concepts/paging.md", "Pagination", "Paging through collections"),
    # Batch
    ("batch-requests", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/concepts/json-batching.md", "Batch Requests", "JSON batching"),
    # Auth
    ("auth-overview", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/concepts/auth/auth-concepts.md", "Authentication", "Authentication and authorization basics"),
    ("permissions-reference", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/concepts/permissions-reference.md", "Permissions", "Permissions reference"),
    # Errors
    ("errors", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/concepts/errors.md", "Error Handling", "Microsoft Graph errors"),
    # Applications
    ("application-list", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/application-list.md", "Applications API", "List applications"),
    ("serviceprincipal-list", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/serviceprincipal-list.md", "Applications API", "List service principals"),
    # Teams
    ("team-list", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/team-list.md", "Teams API", "List teams"),
    ("channel-list", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/channel-list.md", "Teams API", "List channels"),
    # Sites / SharePoint
    ("site-list", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/site-list.md", "SharePoint API", "List sites"),
    ("driveitem-list", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/api-reference/v1.0/api/driveitem-list-children.md", "OneDrive API", "List children of driveItem"),
]

# PowerShell cmdlet reference docs - curated content since the PS docs repo structure is complex
POWERSHELL_DOCS = [
    ("ps-connect-mggraph", "https://raw.githubusercontent.com/microsoftgraph/microsoft-graph-docs-contrib/main/concepts/sdks/powershell.md", "PowerShell SDK", "Microsoft Graph PowerShell SDK"),
]

# Manually curated PowerShell reference content for the most-used cmdlets
POWERSHELL_REFERENCE = [
    {
        "slug": "ps-connect-mggraph-ref",
        "category": "PowerShell Cmdlets",
        "title": "Connect-MgGraph — Authentication",
        "content": """# Connect-MgGraph — PowerShell Authentication

## Synopsis
Authenticate to Microsoft Graph from PowerShell.

## Installation
```powershell
Install-Module Microsoft.Graph -Scope CurrentUser
Import-Module Microsoft.Graph.Authentication
```

## Interactive Login (delegated)
```powershell
Connect-MgGraph -Scopes "User.Read.All","Group.Read.All"
```

## App-Only (certificate)
```powershell
Connect-MgGraph -ClientId "YOUR_APP_ID" -TenantId "YOUR_TENANT_ID" -CertificateThumbprint "CERT_THUMBPRINT"
```

## App-Only (client secret)
```powershell
$secret = ConvertTo-SecureString "YOUR_SECRET" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential("YOUR_APP_ID", $secret)
Connect-MgGraph -TenantId "YOUR_TENANT_ID" -ClientSecretCredential $credential
```

## Managed Identity (Azure)
```powershell
Connect-MgGraph -Identity
```

## Check Connection
```powershell
Get-MgContext
```

## Common Scopes
- User.Read.All — Read all users
- User.ReadWrite.All — Read/write all users
- Group.Read.All — Read all groups
- Group.ReadWrite.All — Read/write all groups
- Mail.Read — Read user mail
- Mail.Send — Send mail as user
- Directory.Read.All — Read directory data
- Application.Read.All — Read applications

## Disconnect
```powershell
Disconnect-MgGraph
```
"""
    },
    {
        "slug": "ps-get-mguser-ref",
        "category": "PowerShell Cmdlets",
        "title": "Get-MgUser — Query Users",
        "content": """# Get-MgUser — Query Users

## Synopsis
Get users from Microsoft Entra ID (Azure AD).

## Get All Users
```powershell
Get-MgUser -All
```

## Get Specific User by ID or UPN
```powershell
Get-MgUser -UserId "user@contoso.com"
Get-MgUser -UserId "12345678-1234-1234-1234-123456789012"
```

## Select Specific Properties
```powershell
Get-MgUser -All -Property "DisplayName,Mail,Department,JobTitle,Id" | Select-Object DisplayName, Mail, Department, JobTitle, Id
```

## Filter Users
```powershell
# By department
Get-MgUser -Filter "department eq 'Engineering'" -All

# By display name starts with
Get-MgUser -Filter "startsWith(displayName, 'John')" -All

# By account enabled
Get-MgUser -Filter "accountEnabled eq true" -All

# By user type (Member vs Guest)
Get-MgUser -Filter "userType eq 'Member'" -All

# By company name
Get-MgUser -Filter "companyName eq 'Contoso'" -All

# Combine filters with 'and'
Get-MgUser -Filter "department eq 'Engineering' and accountEnabled eq true" -All
```

## Search (fuzzy, requires ConsistencyLevel)
```powershell
Get-MgUser -Search '"displayName:john"' -ConsistencyLevel eventual -CountVariable userCount
```

## Sort/Order
```powershell
Get-MgUser -All -Sort "displayName" -ConsistencyLevel eventual
```

## Count
```powershell
Get-MgUser -ConsistencyLevel eventual -CountVariable userCount
Write-Host "Total users: $userCount"
```

## Pagination (Top)
```powershell
Get-MgUser -Top 10
```

## Export to CSV
```powershell
Get-MgUser -All -Property "DisplayName,Mail,Department" | Select-Object DisplayName, Mail, Department | Export-Csv -Path "users.csv" -NoTypeInformation
```

## Common Properties
- Id — GUID
- DisplayName — Full name
- Mail — Primary email
- UserPrincipalName — UPN (login name)
- Department — Department name
- JobTitle — Job title
- AccountEnabled — Boolean
- UserType — Member or Guest
- CompanyName — Company
- CreatedDateTime — When created
- SignInActivity — Last sign-in (requires AuditLog.Read.All)

## Required Permissions
- User.Read.All (Application or Delegated)
"""
    },
    {
        "slug": "ps-get-mggroup-ref",
        "category": "PowerShell Cmdlets",
        "title": "Get-MgGroup — Query Groups",
        "content": """# Get-MgGroup — Query Groups

## Synopsis
Get groups from Microsoft Entra ID.

## Get All Groups
```powershell
Get-MgGroup -All
```

## Get Specific Group
```powershell
Get-MgGroup -GroupId "12345678-1234-1234-1234-123456789012"
```

## Select Properties
```powershell
Get-MgGroup -All -Property "DisplayName,Mail,GroupTypes,SecurityEnabled,Id" | Select-Object DisplayName, Mail, GroupTypes, SecurityEnabled, Id
```

## Filter Groups
```powershell
# Security groups only
Get-MgGroup -Filter "securityEnabled eq true" -All

# Microsoft 365 groups only
Get-MgGroup -Filter "groupTypes/any(g:g eq 'Unified')" -All

# By display name
Get-MgGroup -Filter "displayName eq 'IT Department'" -All

# Starts with
Get-MgGroup -Filter "startsWith(displayName, 'Project')" -All

# Mail-enabled groups
Get-MgGroup -Filter "mailEnabled eq true" -All
```

## Get Group Members
```powershell
Get-MgGroupMember -GroupId "GROUP_ID" -All
```

## Get Group Members with Details
```powershell
Get-MgGroupMember -GroupId "GROUP_ID" -All | ForEach-Object {
    Get-MgUser -UserId $_.Id -Property "DisplayName,Mail" | Select-Object DisplayName, Mail
}
```

## Add Member to Group
```powershell
$params = @{
    "@odata.id" = "https://graph.microsoft.com/v1.0/directoryObjects/{USER_ID}"
}
New-MgGroupMemberByRef -GroupId "GROUP_ID" -BodyParameter $params
```

## Remove Member from Group
```powershell
Remove-MgGroupMemberByRef -GroupId "GROUP_ID" -DirectoryObjectId "USER_ID"
```

## Required Permissions
- Group.Read.All (Application or Delegated)
- GroupMember.Read.All (for members)
- GroupMember.ReadWrite.All (for adding/removing)
"""
    },
    {
        "slug": "ps-new-mguser-ref",
        "category": "PowerShell Cmdlets",
        "title": "New-MgUser — Create Users",
        "content": """# New-MgUser — Create Users

## Synopsis
Create a new user in Microsoft Entra ID.

## Create Basic User
```powershell
$passwordProfile = @{
    Password = "xWwvJ]6NMw+bWH-d"
    ForceChangePasswordNextSignIn = $true
}

$params = @{
    DisplayName = "John Doe"
    MailNickname = "johndoe"
    UserPrincipalName = "johndoe@contoso.com"
    AccountEnabled = $true
    PasswordProfile = $passwordProfile
}

New-MgUser @params
```

## Create User with All Common Properties
```powershell
$params = @{
    DisplayName = "Jane Smith"
    GivenName = "Jane"
    Surname = "Smith"
    MailNickname = "janesmith"
    UserPrincipalName = "janesmith@contoso.com"
    Department = "Engineering"
    JobTitle = "Software Engineer"
    CompanyName = "Contoso"
    OfficeLocation = "Building A, Room 101"
    MobilePhone = "+1-555-0100"
    UsageLocation = "US"
    AccountEnabled = $true
    PasswordProfile = @{
        Password = "xWwvJ]6NMw+bWH-d"
        ForceChangePasswordNextSignIn = $true
    }
}

New-MgUser @params
```

## Bulk Create from CSV
```powershell
$users = Import-Csv -Path "newusers.csv"
foreach ($user in $users) {
    $params = @{
        DisplayName = "$($user.FirstName) $($user.LastName)"
        MailNickname = $user.MailNickname
        UserPrincipalName = "$($user.MailNickname)@contoso.com"
        Department = $user.Department
        JobTitle = $user.JobTitle
        AccountEnabled = $true
        PasswordProfile = @{
            Password = "TempPassword123!"
            ForceChangePasswordNextSignIn = $true
        }
    }
    New-MgUser @params
    Write-Host "Created: $($params.DisplayName)"
}
```

## Required Permissions
- User.ReadWrite.All (Application or Delegated)
"""
    },
    {
        "slug": "ps-update-mguser-ref",
        "category": "PowerShell Cmdlets",
        "title": "Update-MgUser — Modify Users",
        "content": """# Update-MgUser — Modify User Properties

## Synopsis
Update properties of an existing user.

## Update Single Property
```powershell
Update-MgUser -UserId "user@contoso.com" -Department "Marketing"
```

## Update Multiple Properties
```powershell
$params = @{
    Department = "Marketing"
    JobTitle = "Marketing Manager"
    OfficeLocation = "Building B"
    MobilePhone = "+1-555-0200"
}
Update-MgUser -UserId "user@contoso.com" @params
```

## Disable User Account
```powershell
Update-MgUser -UserId "user@contoso.com" -AccountEnabled:$false
```

## Enable User Account
```powershell
Update-MgUser -UserId "user@contoso.com" -AccountEnabled:$true
```

## Bulk Update from CSV
```powershell
$updates = Import-Csv -Path "userupdates.csv"
foreach ($update in $updates) {
    $params = @{
        Department = $update.NewDepartment
        JobTitle = $update.NewTitle
    }
    Update-MgUser -UserId $update.UserPrincipalName @params
    Write-Host "Updated: $($update.UserPrincipalName)"
}
```

## Reset Password
```powershell
$params = @{
    PasswordProfile = @{
        Password = "NewPassword123!"
        ForceChangePasswordNextSignIn = $true
    }
}
Update-MgUser -UserId "user@contoso.com" @params
```

## Required Permissions
- User.ReadWrite.All (Application or Delegated)
"""
    },
    {
        "slug": "ps-common-patterns",
        "category": "PowerShell Patterns",
        "title": "Common Microsoft Graph PowerShell Patterns",
        "content": """# Common Microsoft Graph PowerShell Patterns

## Error Handling
```powershell
try {
    $user = Get-MgUser -UserId "user@contoso.com"
} catch {
    Write-Error "Failed to get user: $($_.Exception.Message)"
    if ($_.Exception.Response.StatusCode -eq 'NotFound') {
        Write-Warning "User not found"
    }
}
```

## Pagination with -All
```powershell
# -All automatically handles pagination
$allUsers = Get-MgUser -All -Property "DisplayName,Mail"

# Without -All, only returns first page (default 100)
$firstPage = Get-MgUser -Top 100
```

## ConsistencyLevel for Advanced Queries
```powershell
# Required for: $search, $count, $filter with 'not', $orderby on certain properties
Get-MgUser -ConsistencyLevel eventual -CountVariable count -Filter "department eq 'IT'" -All
```

## Using -ExpandProperty
```powershell
# Get user with manager
Get-MgUser -UserId "user@contoso.com" -ExpandProperty "manager"

# Get group with members
Get-MgGroup -GroupId "GROUP_ID" -ExpandProperty "members"
```

## Output as JSON
```powershell
Get-MgUser -UserId "user@contoso.com" | ConvertTo-Json -Depth 5
```

## Pipeline to Other Commands
```powershell
# Get all users in IT and disable their accounts
Get-MgUser -Filter "department eq 'IT'" -All | ForEach-Object {
    Update-MgUser -UserId $_.Id -AccountEnabled:$false
}
```

## Direct Graph API Call (when no cmdlet exists)
```powershell
# Use Invoke-MgGraphRequest for endpoints without cmdlets
$response = Invoke-MgGraphRequest -Method GET -Uri "https://graph.microsoft.com/v1.0/users?`$filter=department eq 'Sales'&`$select=displayName,mail"
$response.value
```

## Beta API Access
```powershell
# Switch to beta endpoint
Select-MgProfile -Name "beta"
# or
Get-MgUser -UserId "user@contoso.com" # now uses beta

# Switch back
Select-MgProfile -Name "v1.0"
```

## Module Management
```powershell
# Install specific sub-modules (faster than full Microsoft.Graph)
Install-Module Microsoft.Graph.Authentication -Scope CurrentUser
Install-Module Microsoft.Graph.Users -Scope CurrentUser
Install-Module Microsoft.Graph.Groups -Scope CurrentUser

# Check installed version
Get-Module Microsoft.Graph* -ListAvailable | Select-Object Name, Version

# Update
Update-Module Microsoft.Graph
```
"""
    },
    {
        "slug": "ps-mail-ref",
        "category": "PowerShell Cmdlets",
        "title": "Mail Operations — Send and Read Email",
        "content": """# Microsoft Graph PowerShell — Mail Operations

## Read User's Messages
```powershell
# Get recent messages
Get-MgUserMessage -UserId "user@contoso.com" -Top 10

# Select specific fields
Get-MgUserMessage -UserId "user@contoso.com" -Property "Subject,From,ReceivedDateTime" -Top 10 | Select-Object Subject, @{N='From';E={$_.From.EmailAddress.Address}}, ReceivedDateTime

# Filter by subject
Get-MgUserMessage -UserId "user@contoso.com" -Filter "contains(subject, 'Important')"

# Unread messages only
Get-MgUserMessage -UserId "user@contoso.com" -Filter "isRead eq false" -All
```

## Send Email
```powershell
$params = @{
    Message = @{
        Subject = "Meeting Tomorrow"
        Body = @{
            ContentType = "HTML"
            Content = "<p>Hi, let's meet tomorrow at 10am.</p>"
        }
        ToRecipients = @(
            @{
                EmailAddress = @{
                    Address = "recipient@contoso.com"
                }
            }
        )
    }
}

Send-MgUserMail -UserId "sender@contoso.com" -BodyParameter $params
```

## Send with Attachment
```powershell
$fileContent = [Convert]::ToBase64String([IO.File]::ReadAllBytes("report.pdf"))

$params = @{
    Message = @{
        Subject = "Report Attached"
        Body = @{
            ContentType = "Text"
            Content = "Please see attached report."
        }
        ToRecipients = @(
            @{ EmailAddress = @{ Address = "recipient@contoso.com" } }
        )
        Attachments = @(
            @{
                "@odata.type" = "#microsoft.graph.fileAttachment"
                Name = "report.pdf"
                ContentType = "application/pdf"
                ContentBytes = $fileContent
            }
        )
    }
}

Send-MgUserMail -UserId "sender@contoso.com" -BodyParameter $params
```

## Required Permissions
- Mail.Read — Read messages
- Mail.Send — Send messages
- Mail.ReadWrite — Read/write messages
"""
    },
]


def fetch_doc(url, slug, timeout=30):
    """Fetch a markdown doc from GitHub or learn.microsoft.com."""
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Praxis/1.0 (doc-indexer)"
        })
        if resp.status_code == 200:
            return resp.text
        print(f"  WARN: {slug} returned {resp.status_code}")
        return None
    except Exception as e:
        print(f"  WARN: {slug} fetch failed: {e}")
        return None


def clean_yaml_frontmatter(content):
    """Remove YAML frontmatter from markdown."""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:].strip()
    return content


def chunk_markdown(content, slug, category, title, max_chunk=2000):
    """Split markdown into chunks preserving code blocks and headers.
    
    Strategy: split on ## headers, keeping code blocks intact.
    Each chunk gets the doc title prepended for context.
    """
    content = clean_yaml_frontmatter(content)
    
    # Remove [!INCLUDE...] directives and HTML comments
    content = re.sub(r'\[!INCLUDE\s*\[.*?\]\(.*?\)\]', '', content)
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # Split on ## headers
    sections = re.split(r'\n(?=## )', content)
    
    chunks = []
    for section in sections:
        section = section.strip()
        if not section or len(section) < 50:
            continue
            
        # If section is small enough, keep as one chunk
        if len(section) <= max_chunk:
            chunk_text = f"# {title}\n\n{section}" if not section.startswith("# ") else section
            chunks.append(chunk_text)
        else:
            # Split large sections on ### or code block boundaries
            subsections = re.split(r'\n(?=### )', section)
            current = ""
            for sub in subsections:
                if len(current) + len(sub) > max_chunk and current:
                    chunk_text = f"# {title}\n\n{current}" if not current.startswith("# ") else current
                    chunks.append(chunk_text)
                    current = sub
                else:
                    current = current + "\n\n" + sub if current else sub
            if current.strip():
                chunk_text = f"# {title}\n\n{current}" if not current.startswith("# ") else current
                chunks.append(chunk_text)
    
    # If no chunks were generated (maybe no ## headers), treat whole doc as one chunk
    if not chunks and content.strip():
        if len(content) <= max_chunk:
            chunks = [f"# {title}\n\n{content}"]
        else:
            # Split at paragraph boundaries
            paragraphs = content.split("\n\n")
            current = ""
            for para in paragraphs:
                if len(current) + len(para) > max_chunk and current:
                    chunks.append(f"# {title}\n\n{current}")
                    current = para
                else:
                    current = current + "\n\n" + para if current else para
            if current.strip():
                chunks.append(f"# {title}\n\n{current}")
    
    return chunks


def main():
    MSGRAPH_DIR.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    
    # 1. Fetch and process Graph API docs from GitHub
    print("=" * 60)
    print("Phase 1: MS Graph API Reference Docs")
    print("=" * 60)
    
    for slug, url, category, title in GRAPH_API_DOCS:
        print(f"  Fetching: {title} ({slug})")
        content = fetch_doc(url, slug)
        if content:
            # Cache locally
            cache_file = MSGRAPH_DIR / f"{slug}.md"
            cache_file.write_text(content)
            
            chunks = chunk_markdown(content, slug, category, title)
            for i, chunk_text in enumerate(chunks):
                chunk_id = f"msgraph_{slug}_{i}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "source": "MS Graph API",
                    "category": category,
                    "title": title,
                    "slug": slug,
                })
            print(f"    -> {len(chunks)} chunks")
        else:
            print(f"    -> SKIPPED (fetch failed)")
    
    # 2. Fetch PowerShell SDK overview
    print()
    print("=" * 60)
    print("Phase 2: PowerShell SDK Docs")
    print("=" * 60)
    
    for slug, url, category, title in POWERSHELL_DOCS:
        print(f"  Fetching: {title} ({slug})")
        content = fetch_doc(url, slug)
        if content:
            cache_file = MSGRAPH_DIR / f"{slug}.md"
            cache_file.write_text(content)
            
            chunks = chunk_markdown(content, slug, category, title)
            for i, chunk_text in enumerate(chunks):
                chunk_id = f"msgraph_{slug}_{i}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "source": "MS Graph PowerShell",
                    "category": category,
                    "title": title,
                    "slug": slug,
                })
            print(f"    -> {len(chunks)} chunks")
    
    # 3. Add curated PowerShell reference content
    print()
    print("=" * 60)
    print("Phase 3: Curated PowerShell Cmdlet Reference")
    print("=" * 60)
    
    for ref in POWERSHELL_REFERENCE:
        slug = ref["slug"]
        print(f"  Adding: {ref['title']}")
        chunks = chunk_markdown(ref["content"], slug, ref["category"], ref["title"])
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"msgraph_{slug}_{i}"
            all_chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "source": "MS Graph PowerShell",
                "category": ref["category"],
                "title": ref["title"],
                "slug": slug,
            })
        print(f"    -> {len(chunks)} chunks")
    
    print()
    print(f"Total chunks: {len(all_chunks)}")
    
    # 4. Index into ChromaDB
    print()
    print("Indexing into ChromaDB (msgraph-docs collection)...")
    
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection("msgraph-docs")
    except:
        pass
    
    ef = LocalEmbeddingFunction()
    collection = client.create_collection(name="msgraph-docs", embedding_function=ef)
    
    batch_size = 25
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{
                "source": c["source"],
                "category": c["category"],
                "title": c["title"],
                "slug": c["slug"],
            } for c in batch],
        )
        print(f"  Batch {i//batch_size + 1}: {len(batch)} indexed")
    
    print(f"\nDone! {len(all_chunks)} chunks indexed into 'msgraph-docs'")
    return len(all_chunks)


if __name__ == "__main__":
    main()
