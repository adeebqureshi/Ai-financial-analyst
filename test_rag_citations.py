"""RAG + citations end-to-end check against the LIVE backend.

1. Generates a small PDF with distinctive facts (PyMuPDF, already a core dep).
2. Uploads it through POST /documents/upload (parse -> chunk -> embed -> index).
3. Asks the AI Insights question through POST /chat/stream.
4. Asserts the answer is grounded, ends with a ``Source:`` line, and the
   ``done`` event carries document citations.

Run:  .venv\\Scripts\\python.exe test_rag_citations.py
"""

import json
import sys
import urllib.request
import uuid

BASE = "http://127.0.0.1:8000"

DOC_TEXT = (
    "Globex Quantum Robotics Annual Report 2024\n"
    "In fiscal year 2024, Globex Quantum Robotics reported total revenue of "
    "77.4 billion dollars and net income of 9.9 billion dollars. "
    "Operating cash flow was 12.1 billion dollars and total debt was "
    "3.2 billion dollars."
)
QUESTION = (
    "According to the annual report, what was the revenue and net income "
    "of Globex Quantum Robotics in fiscal 2024?"
)


def make_pdf(text: str) -> bytes:
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


def upload(pdf: bytes) -> dict:
    boundary = uuid.uuid4().hex
    filename = "globex-quantum-robotics-ar-2024.pdf"
    parts = []
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        (
            f'Content-Disposition: form-data; name="file"; '
            f'filename="{filename}"\r\n'
            "Content-Type: application/pdf\r\n\r\n"
        ).encode()
    )
    parts.append(pdf)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        f"{BASE}/documents/upload",
        data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read())


def ask(question: str) -> dict:
    body = json.dumps({"message": question}).encode()
    req = urllib.request.Request(
        f"{BASE}/chat/stream",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    done: dict = {}
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read().decode()
    for frame in raw.split("\n\n"):
        if frame.startswith("event: done"):
            for line in frame.split("\n"):
                if line.startswith("data: "):
                    done = json.loads(line[6:])
    return done


failures: list[str] = []

print("[1] uploading test PDF ...")
try:
    up = upload(make_pdf(DOC_TEXT))
    doc_id = up["data"]["document_id"]
    print(f"  OK — document_id={doc_id} chunks={up['data'].get('chunks')}")
except Exception as exc:
    print(f"  FAILED — {type(exc).__name__}: {exc}")
    sys.exit(1)

print("\n[2] asking the AI Insights question (RAG retrieval + synthesis) ...")
try:
    done = ask(QUESTION)
except Exception as exc:
    print(f"  FAILED — {type(exc).__name__}: {exc}")
    sys.exit(1)

message = done.get("message", "")
print(f"  answer: {message[:500]!r}")
print(f"  citations: {json.dumps(done.get('sources'), indent=None)[:500]}")

if "could not complete" in message:
    failures.append("LLM_UNAVAILABLE_MESSAGE returned")
if "77.4" not in message:
    failures.append("answer missing the document's revenue figure (77.4)")
if "Source:" not in message:
    failures.append("answer has no 'Source:' citation line")
if not done.get("sources"):
    failures.append("done event carries no document citations")

print()
if failures:
    print("FAILURES:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("RAG + CITATIONS CHECK PASSED")
