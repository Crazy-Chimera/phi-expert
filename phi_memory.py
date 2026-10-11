"""Atomic JSON memory storage; suitable for a single service instance only."""
import asyncio, json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class JsonMemory:
    def __init__(self, directory: str | Path, max_conversations: int = 100):
        self.directory = Path(directory)
        self.path = self.directory / "phi_memory.json"
        self.max_conversations = max_conversations
        self._lock = asyncio.Lock()
        self.directory.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"conversations": [], "profiles": {}})

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"conversations": [], "profiles": {}}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Memory root must be an object")
        data.setdefault("conversations", [])
        data.setdefault("profiles", {})
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".phi-memory-", suffix=".tmp", dir=self.directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.path)
        except Exception:
            try: os.unlink(tmp)
            except OSError: pass
            raise

    async def add_conversation(self, user_id: str, question: str, answer: str, category: str):
        async with self._lock:
            data = await asyncio.to_thread(self._read)
            item = {"id": str(datetime.now(timezone.utc).timestamp()), "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(), "category": category,
                    "question": question, "answer": answer}
            data["conversations"] = (data["conversations"] + [item])[-self.max_conversations:]
            await asyncio.to_thread(self._write, data)
            return item

    async def get_recent_conversations(self, user_id: str, limit: int = 8):
        async with self._lock:
            data = await asyncio.to_thread(self._read)
            return [x for x in data["conversations"] if x.get("user_id") == user_id][-max(0, limit):]

    async def get_profile(self, user_id: str):
        async with self._lock:
            data = await asyncio.to_thread(self._read)
            value = data["profiles"].get(user_id, {})
            return dict(value) if isinstance(value, dict) else {}

    async def update_profile(self, user_id: str, patch: dict[str, Any]):
        async with self._lock:
            data = await asyncio.to_thread(self._read)
            current = data["profiles"].get(user_id, {})
            if not isinstance(current, dict): current = {}
            current.update(patch)
            current["updated_at"] = datetime.now(timezone.utc).isoformat()
            data["profiles"][user_id] = current
            await asyncio.to_thread(self._write, data)
            return dict(current)

    async def export_memory(self, user_id: str | None = None):
        async with self._lock:
            data = await asyncio.to_thread(self._read)
            if user_id is None: return data
            return {"conversations": [x for x in data["conversations"] if x.get("user_id") == user_id],
                    "profiles": {user_id: data["profiles"].get(user_id, {})}}

    async def clear(self, user_id: str | None = None):
        async with self._lock:
            data = await asyncio.to_thread(self._read)
            if user_id is None: data = {"conversations": [], "profiles": {}}
            else:
                data["conversations"] = [x for x in data["conversations"] if x.get("user_id") != user_id]
                data["profiles"].pop(user_id, None)
            await asyncio.to_thread(self._write, data)
