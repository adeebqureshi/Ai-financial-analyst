import os
import tempfile
os.environ.setdefault("AUTH_ENABLED", "false")
_default_auth_db = os.path.join(
    tempfile.gettempdir(),
    "ai-financial-analyst-test-auth.db",
).replace("\\", "/")
os.environ.setdefault("AUTH_DATABASE_URL", f"sqlite:///{_default_auth_db}")
_default_chat_db = os.path.join(
    tempfile.gettempdir(),
    "ai-financial-analyst-test-chat.db",
).replace("\\\\", "/")
os.environ.setdefault("CHAT_DATABASE_URL", f"sqlite:///{_default_chat_db}")