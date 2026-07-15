from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
STATS_PATH = ROOT / "data" / "stats.json"
HTML_PATH = ROOT / "index.html"

REQUIRED_TOP_LEVEL = {
    "meta",
    "summary",
    "clean_curve",
    "live_status",
    "model_match",
    "execution_guard",
    "execution_quality",
    "guard_activity",
    "current_guard_stats",
    "performance_windows",
    "performance_breakdowns",
    "time_filter_what_if",
    "decision_queue",
    "recent_trades",
}

FORBIDDEN_KEY_PARTS = {
    "account_index",
    "api_key",
    "private_key",
    "secret_summary",
    "order_id",
    "client_order_id",
    "client_id",
    "trade_id",
    "raw_order",
    "raw_fill",
    "exchange_payload",
}

FORBIDDEN_VALUE_PATTERNS = [
    re.compile(r"\b730718\b"),
    re.compile(r"\bapi[_ -]?key[_ -]?index\b", re.IGNORECASE),
    re.compile(r"\bprivate[_ -]?key\b", re.IGNORECASE),
    re.compile(r"\bclient[_ -]?order[_ -]?id\b", re.IGNORECASE),
    re.compile(r"\border[_ -]?id\b", re.IGNORECASE),
    re.compile(r"\btrade[_ -]?id\b", re.IGNORECASE),
    re.compile(r"\b0x[a-fA-F0-9]{40,}\b"),
    re.compile(r"\b[a-fA-F0-9]{64,}\b"),
]


def as_float(value: Any, default: float = 0.0) -> float:
    if value in ("", None):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if result == result and result not in (float("inf"), float("-inf")) else default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(as_float(value, float(default)))
    except (TypeError, ValueError):
        return default


def assert_close(label: str, left: Any, right: Any, tolerance: float = 0.01) -> None:
    if abs(as_float(left) - as_float(right)) > tolerance:
        fail(f"{label} mismatch: {left} vs {right}")


def fail(message: str) -> None:
    print(f"VALIDATION FAILED: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> Any:
    if not path.exists():
        fail(f"missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def walk_json(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    rows = [(path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            rows.extend(walk_json(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(walk_json(child, f"{path}[{index}]"))
    return rows


def validate_public_stats(stats: dict[str, Any]) -> None:
    if not isinstance(stats, dict):
        fail("stats payload must be a JSON object")

    missing = sorted(REQUIRED_TOP_LEVEL - set(stats))
    if missing:
        fail(f"stats missing top-level keys: {', '.join(missing)}")

    summary = stats.get("summary") or {}
    trade_count = as_int(summary.get("trade_count"), -1)
    if trade_count < 0:
        fail("summary.trade_count must be non-negative")
    if as_float(summary.get("profit_factor")) < 0:
        fail("summary.profit_factor must be non-negative")

    windows = stats.get("performance_windows") or []
    expected_windows = {"24h", "7d", "30d", "all"}
    actual_windows = {item.get("window") for item in windows if isinstance(item, dict)}
    if expected_windows - actual_windows:
        fail(f"performance_windows missing: {', '.join(sorted(expected_windows - actual_windows))}")
    all_window = next((item for item in windows if isinstance(item, dict) and item.get("window") == "all"), {})
    if all_window:
        if as_int(all_window.get("trade_count"), -1) != trade_count:
            fail("all performance window trade_count must match summary.trade_count")
        assert_close("all performance window net_pnl", all_window.get("net_pnl"), summary.get("net_pnl"))
        assert_close("all performance window profit_factor", all_window.get("profit_factor"), summary.get("profit_factor"), 0.001)

    recent = stats.get("recent_trades") or []
    if not isinstance(recent, list):
        fail("recent_trades must be a list")
    if len(recent) > 30:
        fail("recent_trades must be capped at 30 rows")
    if len(recent) > trade_count:
        fail("recent_trades cannot exceed summary.trade_count")

    curve = stats.get("clean_curve") or {}
    points = curve.get("points") or []
    if not isinstance(points, list):
        fail("clean_curve.points must be a list")
    if len(points) != trade_count + 1:
        fail("clean_curve.points must equal summary.trade_count plus starting point")
    if points:
        assert_close("clean_curve starting equity", points[0].get("equity"), curve.get("starting_equity"))
        assert_close("clean_curve ending equity", points[-1].get("equity"), curve.get("ending_equity"))

    decision_queue = stats.get("decision_queue") or []
    if not isinstance(decision_queue, list) or not decision_queue:
        fail("decision_queue must be a non-empty list")
    for index, item in enumerate(decision_queue):
        if not isinstance(item, dict):
            fail(f"decision_queue[{index}] must be an object")
        for key in ("topic", "status", "priority", "evidence", "next_step"):
            if not item.get(key):
                fail(f"decision_queue[{index}] missing {key}")

    what_if = stats.get("time_filter_what_if") or {}
    candidates = what_if.get("candidates") or []
    if not isinstance(candidates, list) or not candidates:
        fail("time_filter_what_if.candidates must be a non-empty list")
    valid_readiness = {"candidate", "watch only", "too small", "reject"}
    for index, item in enumerate(candidates):
        if item.get("readiness") not in valid_readiness:
            fail(f"time_filter_what_if.candidates[{index}] has invalid readiness")
        if as_int(item.get("removed_count"), -1) < 0:
            fail(f"time_filter_what_if.candidates[{index}] has invalid removed_count")

    for path, value in walk_json(stats):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        if any(part in key for part in FORBIDDEN_KEY_PARTS):
            fail(f"forbidden public key at {path}")
        if isinstance(value, str):
            if path == "$.meta.public_notice":
                continue
            for pattern in FORBIDDEN_VALUE_PATTERNS:
                if pattern.search(value):
                    fail(f"forbidden-looking value at {path}")


def validate_html(html: str) -> None:
    ids = set(re.findall(r'id="([^"]+)"', html))
    refs = set(re.findall(r'byId\("([^"]+)"\)', html))
    missing = sorted(refs - ids)
    if missing:
        fail(f"HTML references missing ids: {', '.join(missing)}")

    required_ids = {
        "alertRows",
        "decisionRows",
        "healthRows",
        "performanceWindowRows",
        "filterCandidateRows",
        "tradeRows",
    }
    missing_required = sorted(required_ids - ids)
    if missing_required:
        fail(f"HTML missing dashboard ids: {', '.join(missing_required)}")


def main() -> None:
    stats = load_json(STATS_PATH)
    validate_public_stats(stats)
    if not HTML_PATH.exists():
        fail(f"missing {HTML_PATH}")
    validate_html(HTML_PATH.read_text(encoding="utf-8"))
    print("Public stats validation passed.")


if __name__ == "__main__":
    main()
