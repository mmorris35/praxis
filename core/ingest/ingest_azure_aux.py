#!/usr/bin/env python3
"""Ingest Azure + auxiliary Microsoft docs into Praxis ChromaDB collections."""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import chromadb

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.gateway.rag import LocalEmbeddingFunction

CHROMA_DIR = Path(__file__).parent.parent.parent / "examples" / "cmmc-buddy" / "data" / "chroma"
WORK_DIR = Path("/tmp/praxis-azure-ingest")

SOURCES = [
    {
        "name": "azure-monitor-sentinel",
        "repo": "https://github.com/MicrosoftDocs/azure-docs.git",
        "sparse_paths": [
            "articles/azure-monitor",
            "articles/sentinel",
            "articles/data-explorer/kusto/query",
        ],
        "use_sparse": True,
    },
    {
        "name": "m365-dsc",
        "repo": "https://github.com/microsoft/Microsoft365DSC.git",
        "doc_paths": ["docs/docs/resources", "docs/docs/user-guide"],
    },
    {
        "name": "cisa-scuba",
        "repo": "https://github.com/cisagov/ScubaGear.git",
        "doc_paths": ["docs", "PowerShell/ScubaGear/baselines"],
    },
    {
        "name": "exchange-powershell",
        "repo": "https://github.com/MicrosoftDocs/office-docs-powershell.git",
        "doc_paths": ["exchange"],
    },
    {
        "name": "azure-policy",
        "repo": "https://github.com/Azure/azure-policy.git",
        "doc_paths": ["built-in-policies"],
        "extensions": [".md", ".json"],
    },
    {
        "name": "sharepoint-pnp",
        "repo": "https://github.com/pnp/powershell.git",
        "doc_paths": ["documentation"],
    },
    {
        "name": "azure-cli",
        "repo": "https://github.com/MicrosoftDocs/azure-docs-cli.git",
        "doc_paths": ["docs-ref-conceptual"],
    },
]


def clone_repo(repo_url, dest, sparse_paths=None):
    """Clone a repo. Use sparse checkout if sparse_paths provided."""
    if dest.exists():
        subprocess.run(["rm", "-rf", str(dest)])

    if sparse_paths:
        r = subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", repo_url, str(dest)],
            capture_output=True, timeout=180,
        )
        if r.returncode != 0:
            print(f"    Clone failed: {r.stderr.decode()[:200]}")
            return False
        subprocess.run(
            ["git", "sparse-checkout", "set"] + sparse_paths,
            cwd=str(dest), capture_output=True, timeout=120,
        )
    else:
        r = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(dest)],
            capture_output=True, timeout=300,
        )
        if r.returncode != 0:
            print(f"    Clone failed: {r.stderr.decode()[:200]}")
            return False
    return dest.exists()


def chunk_text(text, max_size=2000):
    """Split text into chunks, preserving code blocks."""
    chunks = []
    sections = re.split(r'(?=^#{1,3}\s)', text, flags=re.MULTILINE)

    current = ""
    for section in sections:
        if not section.strip():
            continue
        if len(current) + len(section) <= max_size:
            current += section
        else:
            if current.strip():
                chunks.append(current.strip())
            if len(section) > max_size:
                parts = re.split(r'\n\n(?!```)', section)
                sub = ""
                for part in parts:
                    if len(sub) + len(part) <= max_size:
                        sub += "\n\n" + part
                    else:
                        if sub.strip():
                            chunks.append(sub.strip())
                        sub = part
                if sub.strip():
                    chunks.append(sub.strip())
                current = ""
            else:
                current = section

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [text[:max_size]]


def walk_docs(base_path, doc_paths, extensions=None):
    """Walk directories and yield (filepath, content) for docs."""
    if extensions is None:
        extensions = [".md"]

    for doc_path in doc_paths:
        full = base_path / doc_path
        if not full.exists():
            print(f"    Path not found: {full}, skipping")
            continue
        for root, dirs, files in os.walk(full):
            for f in files:
                if any(f.endswith(ext) for ext in extensions):
                    fp = Path(root) / f
                    try:
                        content = fp.read_text(errors="ignore")
                        if len(content.strip()) > 50:
                            yield fp, content
                    except Exception:
                        pass


def ingest_source(source, client, ef):
    """Ingest one source into its own ChromaDB collection."""
    name = source["name"]
    repo = source["repo"]
    dest = WORK_DIR / name

    print(f"\n{'='*60}")
    print(f"Ingesting: {name}")
    print(f"Repo: {repo}")

    sparse = source.get("sparse_paths")
    use_sparse = source.get("use_sparse", False)

    if use_sparse and sparse:
        ok = clone_repo(repo, dest, sparse_paths=sparse)
    else:
        ok = clone_repo(repo, dest)

    if not ok:
        print(f"  FAILED to clone {repo}, skipping")
        return 0

    doc_paths = source.get("doc_paths", sparse or ["."])
    extensions = source.get("extensions", [".md"])

    all_chunks = []
    file_count = 0
    for fp, content in walk_docs(dest, doc_paths, extensions):
        file_count += 1
        rel = str(fp.relative_to(dest))
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            chunk_id = re.sub(r'[^a-zA-Z0-9_.-]', '_', f"{name}_{rel}_{i}")[:200]
            all_chunks.append({
                "id": chunk_id,
                "text": chunk,
                "source": name,
                "file": rel,
            })

    if not all_chunks:
        print(f"  No documents found, skipping")
        subprocess.run(["rm", "-rf", str(dest)])
        return 0

    print(f"  Files: {file_count}, Chunks: {len(all_chunks)}")

    try:
        client.delete_collection(name)
    except Exception:
        pass

    collection = client.create_collection(name=name, embedding_function=ef)

    batch_size = 500
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{"source": c["source"], "file": c["file"]} for c in batch],
        )
        done = min(i + batch_size, len(all_chunks))
        print(f"  Indexed {done}/{len(all_chunks)}")

    subprocess.run(["rm", "-rf", str(dest)])
    print(f"  Done: {len(all_chunks)} chunks in '{name}'")
    return len(all_chunks)


def run_smoke_tests(client, ef):
    """Run smoke test queries against all collections."""
    queries = [
        ("azure-monitor-sentinel", "KQL query to find failed sign-in attempts"),
        ("m365-dsc", "Microsoft365DSC export current tenant configuration"),
        ("cisa-scuba", "CISA SCuBA baseline for Exchange Online"),
        ("exchange-powershell", "New-TransportRule Exchange Online PowerShell"),
        ("azure-policy", "Azure Policy audit vs deny effect"),
        ("sharepoint-pnp", "Connect-PnPOnline authentication methods"),
        ("azure-cli", "az keyvault secret set syntax"),
    ]

    print(f"\n{'='*60}")
    print("SMOKE TESTS")
    print(f"{'='*60}")

    for coll_name, query in queries:
        try:
            col = client.get_collection(coll_name, embedding_function=ef)
            results = col.query(query_texts=[query], n_results=3)
            print(f"\nQUERY [{coll_name}]: {query}")
            if results["ids"][0]:
                for i in range(min(3, len(results["ids"][0]))):
                    d = results["distances"][0][i]
                    doc = results["documents"][0][i][:150].replace("\n", " ")
                    print(f"  #{i+1} dist={d:.3f} | {doc}...")
                print("  PASS")
            else:
                print("  FAIL -- no results")
        except Exception as e:
            print(f"\nQUERY [{coll_name}]: {query}")
            print(f"  SKIP -- collection not available: {e}")


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    print("Praxis Azure + Auxiliary Docs Ingest")
    print(f"ChromaDB: {CHROMA_DIR}")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = LocalEmbeddingFunction()

    total = 0
    results = {}
    start = time.time()

    for source in SOURCES:
        count = ingest_source(source, client, ef)
        results[source["name"]] = count
        total += count

    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print(f"INGEST COMPLETE -- {total} total chunks in {elapsed:.0f}s")
    for name, count in results.items():
        print(f"  {name}: {count}")
    print(f"{'='*60}")

    run_smoke_tests(client, ef)


if __name__ == "__main__":
    main()
