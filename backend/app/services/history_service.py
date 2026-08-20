"""Local Analysis History and Scan Persistence Service."""

from datetime import datetime, timezone
import json
import os
import threading
from typing import Any, Dict, List, Optional
from app.models.schemas import ScanHistorySummary

HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".codesanitize_history")
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")


class HistoryService:
    """Manages local persistent history of single-file and project-level code analysis scans."""

    _lock = threading.Lock()

    @classmethod
    def _ensure_storage(cls):
        """Ensure the history directory and JSON file exist."""
        if not os.path.exists(HISTORY_DIR):
            os.makedirs(HISTORY_DIR, exist_ok=True)
        if not os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    @classmethod
    def save_scan(
        cls,
        scan_id: str,
        target_name: str,
        scan_type: str,
        language: str,
        score: int,
        lines_of_code: int,
        findings_count: int,
        critical_security_count: int,
        status: str,
        full_payload: Dict[str, Any],
    ) -> str:
        """Persist a completed scan into local history."""
        cls._ensure_storage()
        record = {
            "scan_id": scan_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_name": target_name,
            "scan_type": scan_type,
            "language": language,
            "score": score,
            "lines_of_code": lines_of_code,
            "findings_count": findings_count,
            "critical_security_count": critical_security_count,
            "status": status,
            "payload": full_payload,
        }

        with cls._lock:
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

            # Prepend newest scan and keep last 200 scans
            history.insert(0, record)
            history = history[:200]

            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)

        return scan_id

    @classmethod
    def list_scans(cls, limit: int = 50) -> List[ScanHistorySummary]:
        """List scan summaries ordered by newest first."""
        cls._ensure_storage()
        with cls._lock:
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        summaries: List[ScanHistorySummary] = []
        for item in history[:limit]:
            try:
                ts = datetime.fromisoformat(item["timestamp"])
            except Exception:
                ts = datetime.now(timezone.utc)

            summaries.append(
                ScanHistorySummary(
                    scan_id=item["scan_id"],
                    timestamp=ts,
                    target_name=item.get("target_name", "Untitled"),
                    scan_type=item.get("scan_type", "single_file"),
                    language=item.get("language", "python"),
                    score=item.get("score", 0),
                    lines_of_code=item.get("lines_of_code", 0),
                    findings_count=item.get("findings_count", 0),
                    critical_security_count=item.get("critical_security_count", 0),
                    status=item.get("status", "completed"),
                )
            )
        return summaries

    @classmethod
    def get_scan(cls, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full scan details by scan ID."""
        cls._ensure_storage()
        with cls._lock:
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                return None

        for item in history:
            if item.get("scan_id") == scan_id:
                return item.get("payload")
        return None

    @classmethod
    def delete_scan(cls, scan_id: str) -> bool:
        """Delete a scan from history by ID."""
        cls._ensure_storage()
        with cls._lock:
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                return False

            orig_len = len(history)
            history = [item for item in history if item.get("scan_id") != scan_id]
            if len(history) < orig_len:
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(history, f, indent=2)
                return True
        return False

    @classmethod
    def clear_history(cls) -> bool:
        """Clear all history records."""
        cls._ensure_storage()
        with cls._lock:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
        return True
