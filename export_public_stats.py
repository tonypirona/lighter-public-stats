from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
FREQTRADE_ROOT = ROOT.parent / "freqtrade"
LIVE_STATE = FREQTRADE_ROOT / "user_data" / "live_state"
LIVE_REPORTS = FREQTRADE_ROOT / "user_data" / "live_reports"

TRACKER_PATH = LIVE_STATE / "lighter_tracker_trades.json"
ACCOUNT_PATH = LIVE_STATE / "lighter_account_status.json"
HEARTBEAT_PATH = LIVE_STATE / "lighter_live_monitor_heartbeat.json"
WATCHDOG_PATH = LIVE_STATE / "lighter_live_watchdog_status.json"
EXPECTED_PATH = LIVE_REPORTS / "lighter_expected_vs_actual_summary.json"
OUT_PATH = ROOT / "data" / "stats.json"

START_EQUITY = 100.0
CLEAN_LEVERAGE = 25.0
NOTIONAL_CAP = 5000.0
DUST_QTY = 0.0001
PUBLIC_HEARTBEAT_MINUTES = 15


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def number(value: Any, default: float = 0.0) -> float:
    if value in ("", None):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: Any) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def public_time(value: Any) -> str:
    parsed = parse_time(value)
    if parsed.year == 1:
        return ""
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def trade_return_pct(trade: dict[str, Any]) -> float:
    notional = abs(number(trade.get("notional")))
    pnl = number(trade.get("pnl"))
    if notional > 0:
        return pnl / notional * 100.0

    entry = number(trade.get("entry"))
    exit_price = number(trade.get("exit"))
    if entry <= 0 or exit_price <= 0:
        return 0.0
    direction = -1.0 if str(trade.get("side")).lower() == "short" else 1.0
    return (exit_price - entry) / entry * 100.0 * direction


def should_publish_trade(trade: dict[str, Any]) -> bool:
    if str(trade.get("source", "")).lower() != "bot":
        return False
    if str(trade.get("status", "")).lower() != "closed":
        return False
    if trade.get("excluded") is True:
        return False
    if abs(number(trade.get("qty"))) < DUST_QTY:
        return False
    notes = str(trade.get("notes", "")).lower()
    tags = str(trade.get("tags", "")).lower()
    if "bug-related" in notes or "incident" in tags:
        return False
    return True


def profit_factor(pnls: list[float]) -> float:
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    if gross_loss == 0:
        return gross_profit if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def max_drawdown(points: list[dict[str, Any]]) -> tuple[float, float]:
    peak = START_EQUITY
    worst_dollar = 0.0
    worst_pct = 0.0
    for point in points:
        equity = number(point.get("equity"), START_EQUITY)
        peak = max(peak, equity)
        drawdown = peak - equity
        drawdown_pct = drawdown / peak * 100.0 if peak else 0.0
        worst_dollar = max(worst_dollar, drawdown)
        worst_pct = max(worst_pct, drawdown_pct)
    return worst_dollar, worst_pct


def clean_curve(trades: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], float]:
    equity = START_EQUITY
    points: list[dict[str, Any]] = [
        {"time": "", "equity": round(equity, 4), "pnl": 0.0, "return_pct": 0.0}
    ]
    for trade in trades:
        ret_pct = trade_return_pct(trade)
        exposure = min(equity * CLEAN_LEVERAGE, NOTIONAL_CAP)
        pnl = exposure * ret_pct / 100.0
        equity += pnl
        points.append(
            {
                "time": public_time(trade.get("closedAt") or trade.get("openedAt")),
                "equity": round(equity, 4),
                "pnl": round(pnl, 4),
                "return_pct": round(ret_pct, 5),
            }
        )
    return points, equity


def avg(values: list[float]) -> float:
    values = [value for value in values if not math.isnan(value) and not math.isinf(value)]
    return sum(values) / len(values) if values else 0.0


def compact_expected(summary: dict[str, Any]) -> dict[str, Any]:
    allowed = [
        "generated_at_utc",
        "since_utc",
        "until_utc",
        "model",
        "closed_bot_trades",
        "expected_model_trades",
        "filled_expected_entries",
        "missing_expected_entries",
        "blocked_expected_entries",
        "sent_no_fill_entries",
        "unexpected_live_entries",
        "actual_pnl_sum",
        "actual_return_pct_sum",
        "actual_return_profit_factor",
        "return_delta_pct_sum",
        "avg_return_delta_bp",
        "current_paper_status",
        "current_paper_action",
    ]
    public: dict[str, Any] = {}
    for key in allowed:
        if key in summary:
            public[key] = summary[key]
    return public


def comparable_payload(payload: dict[str, Any]) -> dict[str, Any]:
    comparable = json.loads(json.dumps(payload, sort_keys=True))
    meta = comparable.get("meta", {})
    meta.pop("generated_at_utc", None)
    meta.pop("tracker_synced_at_utc", None)
    return comparable


def main() -> None:
    tracker = read_json(TRACKER_PATH, {})
    account = read_json(ACCOUNT_PATH, {})
    heartbeat = read_json(HEARTBEAT_PATH, {})
    watchdog = read_json(WATCHDOG_PATH, {})
    expected = read_json(EXPECTED_PATH, {})

    raw_trades = tracker.get("trades") or []
    published_trades = sorted(
        [trade for trade in raw_trades if isinstance(trade, dict) and should_publish_trade(trade)],
        key=lambda item: parse_time(item.get("closedAt") or item.get("openedAt")),
    )

    pnls = [number(trade.get("pnl")) for trade in published_trades]
    returns = [trade_return_pct(trade) for trade in published_trades]
    spreads = [number(trade.get("spreadBp"), math.nan) for trade in published_trades if trade.get("spreadBp") not in ("", None)]
    slippages = [number(trade.get("slippageBp"), math.nan) for trade in published_trades if trade.get("slippageBp") not in ("", None)]
    execution_costs = [
        number(trade.get("executionCostBp"), math.nan)
        for trade in published_trades
        if trade.get("executionCostBp") not in ("", None)
    ]

    curve_points, ending_equity = clean_curve(published_trades)
    dd_dollar, dd_pct = max_drawdown(curve_points)

    latest_account = account.get("account") or tracker.get("account_status") or {}
    position = account.get("btc_position") or tracker.get("bot_open_position") or {}
    live_status = tracker.get("live_status") or {}

    recent = []
    for trade in reversed(published_trades[-30:]):
        recent.append(
            {
                "opened_at": public_time(trade.get("openedAt")),
                "closed_at": public_time(trade.get("closedAt")),
                "market": trade.get("market", "BTCUSDC.P"),
                "side": str(trade.get("side", "")).lower(),
                "status": trade.get("status", ""),
                "order_type": trade.get("orderType") or trade.get("entryOrderType") or "",
                "role": f"{trade.get('entryRole', '')} -> {trade.get('exitRole', '')}".strip(),
                "entry": round(number(trade.get("entry")), 2),
                "exit": round(number(trade.get("exit")), 2),
                "qty": round(number(trade.get("qty")), 6),
                "notional": round(number(trade.get("notional")), 2),
                "pnl": round(number(trade.get("pnl")), 4),
                "return_pct": round(trade_return_pct(trade), 5),
                "spread_bp": round(number(trade.get("spreadBp")), 4),
                "slippage_bp": round(number(trade.get("slippageBp")), 4),
                "execution_cost_bp": round(number(trade.get("executionCostBp")), 4),
                "exit_reason": trade.get("exitReason", ""),
            }
        )

    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    net_pnl = sum(pnls)

    payload = {
        "meta": {
            "generated_at_utc": iso_now(),
            "source": "sanitized local export",
            "public_notice": "No API keys, account index, order IDs, client IDs, or raw exchange payloads are included.",
            "tracker_synced_at_utc": tracker.get("synced_at_utc") or account.get("checked_at_utc") or "",
            "market": "BTCUSDC.P",
        },
        "summary": {
            "trade_count": len(published_trades),
            "net_pnl": round(net_pnl, 4),
            "win_rate_pct": round(len(wins) / len(published_trades) * 100.0, 2) if published_trades else 0.0,
            "profit_factor": round(profit_factor(pnls), 4),
            "avg_trade_pnl": round(avg(pnls), 4),
            "avg_trade_return_pct": round(avg(returns), 5),
            "gross_profit": round(sum(wins), 4),
            "gross_loss": round(sum(losses), 4),
            "avg_spread_bp": round(avg(spreads), 4),
            "avg_slippage_bp": round(avg(slippages), 4),
            "avg_execution_cost_bp": round(avg(execution_costs), 4),
        },
        "clean_curve": {
            "starting_equity": START_EQUITY,
            "leverage": CLEAN_LEVERAGE,
            "notional_cap": NOTIONAL_CAP,
            "ending_equity": round(ending_equity, 4),
            "net_pct": round((ending_equity / START_EQUITY - 1.0) * 100.0, 2),
            "max_drawdown": round(dd_dollar, 4),
            "max_drawdown_pct": round(dd_pct, 2),
            "points": curve_points,
        },
        "live_status": {
            "monitor_ok": bool((heartbeat.get("ok") is True) or (live_status.get("monitor_ok") is True)),
            "watchdog_ok": bool((watchdog.get("ok") is True) or (live_status.get("watchdog_ok") is True)),
            "live_enabled": bool((account.get("secret_summary") or {}).get("live_enabled") or live_status.get("live_enabled")),
            "paper_status": live_status.get("paper_status") or expected.get("current_paper_status") or "",
            "paper_action": live_status.get("paper_action") or expected.get("current_paper_action") or "",
            "position_side": position.get("side", "flat"),
            "position_btc_abs": number(position.get("position_btc_abs")),
            "available_balance": number(latest_account.get("available_balance")),
            "total_asset_value": number(latest_account.get("total_asset_value")),
            "pending_order_count": int(number(latest_account.get("pending_order_count"))),
        },
        "model_match": compact_expected(expected),
        "recent_trades": recent,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing_payload = read_json(OUT_PATH, {})
    if existing_payload and comparable_payload(existing_payload) == comparable_payload(payload):
        existing_stamp = parse_time((existing_payload.get("meta") or {}).get("generated_at_utc"))
        if existing_stamp.year != 1 and datetime.now(timezone.utc) - existing_stamp < timedelta(minutes=PUBLIC_HEARTBEAT_MINUTES):
            print(f"No public stat changes. Kept {OUT_PATH}")
            return
        print(f"No stat changes, but public heartbeat is older than {PUBLIC_HEARTBEAT_MINUTES} minutes.")

    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(
        f"Trades={len(published_trades)} net=${net_pnl:.2f} PF={payload['summary']['profit_factor']:.2f} "
        f"clean_25x={payload['clean_curve']['net_pct']:.2f}%"
    )


if __name__ == "__main__":
    main()
