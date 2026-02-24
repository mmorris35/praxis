from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from pathlib import Path
from collections import defaultdict
import time, uuid, traceback, os, re, logging, json

# Load .env file if present
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from gateway.rag import retrieve, format_context, extract_sources
from gateway.llm import chat
from gateway.amp import recall, learn, format_lessons_for_prompt

# --- Logging ---
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
security_log = logging.getLogger("jmo.security")
security_log.setLevel(logging.INFO)
_handler = logging.FileHandler(LOG_DIR / "security.log")
_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
security_log.addHandler(_handler)

app = FastAPI(title="JMO — AMP Gateway", docs_url=None, redoc_url=None, openapi_url=None)

# --- Security layers ---

# 1. Rate limiting (per IP) — tiered
_rate_limits: dict[str, list[float]] = defaultdict(list)
RATE_WINDOW = 60  # seconds
RATE_CHAT = int(os.environ.get("JMO_RATE_CHAT", "15"))       # chat requests/min
RATE_CORRECT = int(os.environ.get("JMO_RATE_CORRECT", "5"))  # corrections/min
RATE_GLOBAL = int(os.environ.get("JMO_RATE_GLOBAL", "5"))    # any endpoint/min for banned IPs

# Auto-ban: IPs that hit honeypot paths or too many 404s
_banned_ips: dict[str, float] = {}  # ip -> ban_until timestamp
_fourohfour_counts: dict[str, list[float]] = defaultdict(list)
BAN_DURATION = 3600  # 1 hour
FOUROHFOUR_THRESHOLD = 10  # 10 404s in 60 seconds = ban

def _is_banned(ip: str) -> bool:
    if ip in _banned_ips:
        if time.time() < _banned_ips[ip]:
            return True
        del _banned_ips[ip]
    return False

def _ban_ip(ip: str, reason: str):
    _banned_ips[ip] = time.time() + BAN_DURATION
    security_log.warning(f"BANNED ip={ip} reason={reason} duration={BAN_DURATION}s")

def _check_rate_limit(ip: str, bucket: str = "chat", limit: int = None) -> bool:
    if limit is None:
        limit = RATE_CHAT
    key = f"{bucket}:{ip}"
    now = time.time()
    _rate_limits[key] = [t for t in _rate_limits[key] if now - t < RATE_WINDOW]
    if len(_rate_limits[key]) >= limit:
        return False
    _rate_limits[key].append(now)
    return True

# 2. Input sanitization — expanded injection patterns
INJECTION_PATTERNS = [
    re.compile(r'ignore\s+(all\s+)?(previous|prior|above|your)\s+(instructions|prompts|rules)', re.I),
    re.compile(r'(system|admin|developer|internal)\s*prompt', re.I),
    re.compile(r'you\s+are\s+now\s+', re.I),
    re.compile(r'pretend\s+(you|to)\s+(are|be)\s+', re.I),
    re.compile(r'output\s+(your|the)\s+(system|initial|original|hidden)\s+', re.I),
    re.compile(r'disregard\s+(all|your|the)\s+', re.I),
    re.compile(r'\bDAN\b.*\bjailbreak\b', re.I),
    re.compile(r'reveal\s+(your|the)\s+(instructions|prompt|config)', re.I),
    re.compile(r'(repeat|print|show|display)\s+(everything|all|the)\s+(above|before|system)', re.I),
    re.compile(r'act\s+as\s+(if\s+)?(you\s+)?(are|were)\s+', re.I),
    re.compile(r'new\s+instructions?\s*:', re.I),
    re.compile(r'<\s*/?script', re.I),  # XSS
    re.compile(r'javascript\s*:', re.I),  # XSS
    re.compile(r'on(error|load|click)\s*=', re.I),  # XSS
    re.compile(r'\{\{.*\}\}', re.I),  # template injection
    re.compile(r'\$\{.*\}', re.I),  # template injection
]

def _check_injection(text: str) -> bool:
    return any(p.search(text) for p in INJECTION_PATTERNS)

# 3. Honeypot paths — instant ban for scanning bots
HONEYPOT_PATHS = {
    '/wp-admin', '/wp-login', '/.env', '/config', '/admin',
    '/api/v1/namespaces', '/graphql', '/.git', '/debug',
    '/actuator', '/console', '/manager', '/phpmyadmin',
    '/solr', '/jenkins', '/struts', '/cgi-bin',
    '/wp-content', '/wp-includes', '/xmlrpc.php',
    '/.aws', '/.docker', '/server-status', '/server-info',
    '/api/v1/pods', '/metadata', '/latest/meta-data',
    '/etc/passwd', '/proc/self', '/.well-known/openid',
}

# 4. Correction auth
CORRECTION_KEY = os.environ.get("JMO_CORRECTION_KEY", "")

# 5. Allowed paths (whitelist)
ALLOWED_PATHS = {'/', '/about', '/robots.txt', '/api/health', '/api/chat', '/api/correct', '/v1/chat/completions', '/favicon.ico'}


# --- Middleware ---

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path.rstrip('/')
    method = request.method

    # Check ban list
    if _is_banned(client_ip):
        security_log.info(f"BLOCKED_BANNED ip={client_ip} path={path}")
        return PlainTextResponse("", status_code=403)

    # Honeypot — instant ban
    path_lower = path.lower()
    for hp in HONEYPOT_PATHS:
        if path_lower.startswith(hp):
            _ban_ip(client_ip, f"honeypot:{path}")
            return PlainTextResponse("", status_code=404)

    # Path traversal detection
    if '..' in path or '%2e%2e' in path_lower or '%00' in path_lower:
        _ban_ip(client_ip, f"traversal:{path}")
        security_log.warning(f"TRAVERSAL ip={client_ip} path={path}")
        return PlainTextResponse("", status_code=400)

    # Track 404s — auto-ban scanners
    response = await call_next(request)

    if response.status_code == 404:
        now = time.time()
        _fourohfour_counts[client_ip] = [t for t in _fourohfour_counts[client_ip] if now - t < RATE_WINDOW]
        _fourohfour_counts[client_ip].append(now)
        if len(_fourohfour_counts[client_ip]) >= FOUROHFOUR_THRESHOLD:
            _ban_ip(client_ip, f"404_flood:{len(_fourohfour_counts[client_ip])}_in_60s")

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # Don't leak server info
    if "server" in response.headers:
        del response.headers["server"]

    # Log non-static requests
    if path.startswith("/api") or path.startswith("/v1"):
        security_log.info(f"REQUEST ip={client_ip} method={method} path={path} status={response.status_code}")

    return response


# --- Models ---

class ChatRequest(BaseModel):
    message: str
    session_id: str = ""

class CorrectionRequest(BaseModel):
    question: str
    correction: str
    original_answer: str = ""
    tags: list[str] = []
    key: str = ""

class CompletionMessage(BaseModel):
    role: str
    content: str

class CompletionRequest(BaseModel):
    model: str = ""
    messages: list[CompletionMessage]
    max_tokens: int = 2000
    temperature: float = 0.1


# --- Endpoints ---

@app.get("/api/health")
async def health():
    return {"status": "ok", "name": "JMO", "version": "0.2.0"}


@app.post("/api/chat")
async def api_chat(req: ChatRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"

    # Rate limit
    if not _check_rate_limit(client_ip, "chat", RATE_CHAT):
        security_log.warning(f"RATE_LIMITED ip={client_ip} bucket=chat")
        return JSONResponse(status_code=429, content={"error": "Rate limit exceeded. Try again in a minute."})

    # Injection check
    if _check_injection(req.message):
        security_log.warning(f"INJECTION_BLOCKED ip={client_ip} input={req.message[:100]}")
        return JSONResponse(status_code=400, content={
            "error": "I can only answer mortgage underwriting questions. Please rephrase your question."
        })

    # Length check
    if len(req.message) > 2000:
        return JSONResponse(status_code=400, content={"error": "Question too long. Keep it under 2000 characters."})

    # Empty check
    if len(req.message.strip()) < 3:
        return JSONResponse(status_code=400, content={"error": "Please ask a question."})

    try:
        # Layer 5 (AMP) — Pre-inference recall
        lessons = recall(req.message)
        amp_context = format_lessons_for_prompt(lessons)

        # Layer 1 (RAG) — Retrieve guideline chunks
        chunks = retrieve(req.message)
        rag_context = format_context(chunks)
        sources = extract_sources(chunks)

        # Combine contexts
        full_context = rag_context
        if amp_context:
            full_context = amp_context + "\n\n---\n\n" + rag_context

        # Inference
        response = await chat(req.message, full_context)

        return {
            "response": response,
            "sources": sources,
            "amp_lessons_used": len(lessons),
        }
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": "An error occurred processing your question."})


@app.post("/api/correct")
async def api_correct(req: CorrectionRequest, request: Request):
    """Post-inference: teach the system a correction via AMP."""
    client_ip = request.client.host if request.client else "unknown"

    # Require correction key
    if CORRECTION_KEY and req.key != CORRECTION_KEY:
        security_log.warning(f"BAD_CORRECTION_KEY ip={client_ip}")
        return JSONResponse(status_code=403, content={
            "error": "Correction key required. Only authorized experts can teach JMO."
        })

    # Rate limit corrections strictly
    if not _check_rate_limit(client_ip, "correct", RATE_CORRECT):
        return JSONResponse(status_code=429, content={"error": "Too many corrections. Slow down."})

    # Injection check
    if _check_injection(req.correction) or _check_injection(req.question):
        security_log.warning(f"INJECTION_IN_CORRECTION ip={client_ip}")
        return JSONResponse(status_code=400, content={"error": "Invalid correction content."})

    # Length checks
    if len(req.correction) > 5000 or len(req.question) > 2000:
        return JSONResponse(status_code=400, content={"error": "Content too long."})

    try:
        tags = req.tags if req.tags else ["correction", "underwriting"]
        lesson_id = learn(
            question=req.question,
            correction=req.correction,
            original_answer=req.original_answer,
            tags=tags,
        )
        security_log.info(f"CORRECTION_SAVED ip={client_ip} lesson={lesson_id} question={req.question[:80]}")
        if lesson_id:
            return {"status": "learned", "lesson_id": lesson_id}
        else:
            return JSONResponse(status_code=500, content={"error": "Failed to save lesson"})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": "Failed to save correction."})


@app.post("/v1/chat/completions")
async def openai_compat(req: CompletionRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"

    if not _check_rate_limit(client_ip, "chat", RATE_CHAT):
        return JSONResponse(status_code=429, content={"error": "rate_limit_exceeded"})

    user_msg = ""
    for m in reversed(req.messages):
        if m.role == "user":
            user_msg = m.content
            break

    if _check_injection(user_msg):
        security_log.warning(f"INJECTION_BLOCKED_COMPAT ip={client_ip}")
        return JSONResponse(status_code=400, content={"error": "invalid_request"})

    lessons = recall(user_msg)
    amp_context = format_lessons_for_prompt(lessons)
    chunks = retrieve(user_msg)
    rag_context = format_context(chunks)
    full_context = rag_context
    if amp_context:
        full_context = amp_context + "\n\n---\n\n" + rag_context

    response = await chat(user_msg, full_context)

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response},
            "finish_reason": "stop",
        }],
    }


# --- Admin (locked down) ---

@app.get("/api/admin/bans")
async def admin_bans(request: Request):
    """View banned IPs — only from tailnet."""
    client_ip = request.client.host if request.client else "unknown"
    if not client_ip.startswith("100."):  # Tailscale IPs
        return PlainTextResponse("", status_code=404)
    now = time.time()
    active = {ip: int(until - now) for ip, until in _banned_ips.items() if until > now}
    return {"banned_ips": active, "total": len(active)}


# --- Serve UI ---

ui_dir = Path(__file__).parent.parent / "ui"
if ui_dir.exists():
    @app.get("/")
    async def index():
        return FileResponse(ui_dir / "index.html")

    @app.get("/about")
    async def about():
        return FileResponse(ui_dir / "about.html")

    @app.get("/robots.txt")
    async def robots():
        return FileResponse(ui_dir / "robots.txt", media_type="text/plain")

    @app.get("/favicon.ico")
    async def favicon():
        return PlainTextResponse("", status_code=204)

    app.mount("/ui", StaticFiles(directory=str(ui_dir)), name="ui")
