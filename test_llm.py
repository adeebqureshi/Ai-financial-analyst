"""
Run from your project root:
    python test_llm.py

This bypasses all app wrappers and tests each layer independently.
"""
import os, sys

# ── 1. Load .env ──────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[.env] loaded")
except Exception as e:
    print(f"[.env] FAILED to load: {e}")

# ── 2. Print resolved values ──────────────────────────────────────────────────
base_url = os.getenv("FREELLMAPI_BASE_URL", "")
api_key  = os.getenv("FREELLMAPI_API_KEY", "")
model    = os.getenv("LLM_MODEL", "gpt-4o")
provider = os.getenv("LLM_PROVIDER", "")

print(f"\n[config]")
print(f"  LLM_PROVIDER        = {provider!r}")
print(f"  LLM_MODEL           = {model!r}")
print(f"  FREELLMAPI_BASE_URL = {base_url!r}")
print(f"  FREELLMAPI_API_KEY  = {api_key[:8]!r}... (len={len(api_key)})" if api_key else "  FREELLMAPI_API_KEY  = EMPTY")

if not base_url:
    print("\n[FAIL] FREELLMAPI_BASE_URL is empty — uses_freellmapi will be False, no key will be injected!")
    sys.exit(1)

if not api_key:
    print("\n[FAIL] FREELLMAPI_API_KEY is empty — uses_freellmapi will be False!")
    sys.exit(1)

# ── 3. Raw HTTP test (no openai SDK) ─────────────────────────────────────────
print(f"\n[raw http] POST {base_url}/chat/completions ...")
import urllib.request, json as _json

payload = _json.dumps({
    "model": model,
    "messages": [{"role": "user", "content": "Say: OK"}],
    "max_tokens": 10,
}).encode()

req = urllib.request.Request(
    f"{base_url.rstrip('/')}/chat/completions",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = _json.loads(resp.read())
        print(f"[raw http] SUCCESS — response: {body}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"[raw http] HTTP {e.code} ERROR: {body}")
    sys.exit(1)
except Exception as e:
    print(f"[raw http] CONNECTION ERROR: {type(e).__name__}: {e}")
    sys.exit(1)

# ── 4. OpenAI SDK test ────────────────────────────────────────────────────────
print(f"\n[openai sdk] testing chat.completions.create ...")
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=15)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say: OK"}],
        max_tokens=10,
    )
    print(f"[openai sdk] SUCCESS — {resp.choices[0].message.content!r}")
except Exception as e:
    print(f"[openai sdk] FAILED: {type(e).__name__}: {e}")
    sys.exit(1)

# ── 5. App settings test ──────────────────────────────────────────────────────
print(f"\n[app settings] loading ...")
try:
    sys.path.insert(0, ".")
    from app.core.config import get_settings
    s = get_settings()
    print(f"  uses_freellmapi     = {s.uses_freellmapi}")
    print(f"  freellmapi_base_url = {s.freellmapi_base_url!r}")
    key = s.freellmapi_api_key_str
    print(f"  freellmapi_api_key  = {key[:8]!r}... (len={len(key)})" if key else "  freellmapi_api_key  = EMPTY")
    print(f"  llm_provider        = {s.llm_provider!r}")
    print(f"  llm_model           = {getattr(s, 'llm_model', 'N/A')!r}")
except Exception as e:
    print(f"[app settings] FAILED: {type(e).__name__}: {e}")
    sys.exit(1)

# ── 6. Full app OpenAIClient test ─────────────────────────────────────────────
print(f"\n[app client] testing OpenAIClient.generate ...")
try:
    from app.llm.openai_client import OpenAIClient
    from app.llm.models import LLMRequest
    client = OpenAIClient()
    result = client.generate(LLMRequest(prompt="Say: OK"))
    print(f"[app client] SUCCESS — {result.text!r}")
except Exception as e:
    import traceback
    print(f"[app client] FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n✅ ALL CHECKS PASSED — LLM stack is working correctly.")
