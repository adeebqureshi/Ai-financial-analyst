from __future__ import annotations
import threading
import time
from app.core.config import Settings
_SECONDS_PER_DAY = 86_400
def _day_bucket() -> int:
    return int(time.time() // _SECONDS_PER_DAY)
class TokenQuotaEnforcer:
    def __init__(self, daily_limit: int) -> None:
        self._daily_limit = daily_limit
        self._lock = threading.Lock()
        self._usage: dict[str, int] = {}
    @property
    def enabled(self) -> bool:
        return self._daily_limit > 0
    def consume(self, owner_id: str, tokens: int) -> bool:
        if not self.enabled:
            return True
        key = f"{owner_id}:{_day_bucket()}"
        with self._lock:
            projected = self._usage.get(key, 0) + tokens
            if projected > self._daily_limit:
                return False
            self._usage[key] = projected
        return True
    def remaining(self, owner_id: str) -> int:
        if not self.enabled:
            return -1
        key = f"{owner_id}:{_day_bucket()}"
        with self._lock:
            return max(0, self._daily_limit - self._usage.get(key, 0))
_token_quota: TokenQuotaEnforcer | None = None
_token_quota_lock = threading.Lock()
def get_token_quota(settings: Settings) -> TokenQuotaEnforcer:
    global _token_quota
    with _token_quota_lock:
        if _token_quota is None:
            _token_quota = TokenQuotaEnforcer(
                settings.llm_token_quota_per_user_per_day,
            )
        return _token_quota
def reset_token_quota() -> None:
    global _token_quota
    with _token_quota_lock:
        _token_quota = None