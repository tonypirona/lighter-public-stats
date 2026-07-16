from __future__ import annotations

import csv
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
LEDGER_PATH = LIVE_STATE / "lighter_live_order_ledger.jsonl"
ACCOUNT_PATH = LIVE_STATE / "lighter_account_status.json"
HEARTBEAT_PATH = LIVE_STATE / "lighter_live_monitor_heartbeat.json"
WATCHDOG_PATH = LIVE_STATE / "lighter_live_watchdog_status.json"
EXPECTED_PATH = LIVE_REPORTS / "lighter_expected_vs_actual_summary.json"
ORDER_CONFIG_PATH = LIVE_STATE / "lighter_order_config.json"
PAPER_STATE_PATH = LIVE_STATE / "lighter_native_paper_state.json"
STRATEGY_RESEARCH_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_simple_filter_robustness_decision.json"
STRATEGY_PROMOTION_DECISION_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_candidate_promotion_decision.json"
STRATEGY_TRAIL18_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_trail18_promotion_check_2026_07_16.json"
STRATEGY_TRAIL12_SHORT35_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_trail18_realistic_exit_combo_scan_2026_07_16.json"
STRATEGY_BE_PLATEAU_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_current_model_be_plateau_scan_2026_07_16.json"
STRATEGY_LBE5_SHORT_EXIT_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_lbe5_short_exit_scan_2026_07_16.json"
STRATEGY_SBE10_NET_PRESERVING_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_sbe10_net_preserving_exit_scan_2026_07_16.json"
STRATEGY_SBE10_FAST_CUT_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_sbe10_fast_cut_scan_2026_07_16.json"
STRATEGY_LT8_LIVE_OVERLAP_PATH = FREQTRADE_ROOT / "user_data" / "live_reports" / "lighter_lt8_live_overlap_summary.json"
STRATEGY_LT8_POST_PROMOTION_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_lt8_post_promotion_scan_2026_07_16.json"
STRATEGY_LT6_LBE4_LIVE_OVERLAP_PATH = FREQTRADE_ROOT / "user_data" / "live_reports" / "lighter_lt6_lbe4_live_overlap_summary.json"
STRATEGY_LT6_LBE4_FOLLOWUP_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_lt6_lbe4_followup_scan_2026_07_16.json"
STRATEGY_LT4_LD2_LIVE_OVERLAP_PATH = FREQTRADE_ROOT / "user_data" / "live_reports" / "lighter_lt4_ld2_live_overlap_summary.json"
STRATEGY_LT4_EXECUTION_STRESS_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_tiny_trail_execution_stress_2026_07_16.json"
STRATEGY_LT4_INTRABAR_STRESS_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_intrabar_trail_conservative_check_2026_07_16.json"
STRATEGY_RELAXED_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_relaxed_quality_focused_decision.json"
STRATEGY_RELAXED_CSV_PATH = FREQTRADE_ROOT / "user_data" / "backtest_results" / "lighter_relaxed_quality_focused_scan.csv"
STRATEGY_OVERLAP_PATH = LIVE_REPORTS / "lighter_quality_guard_live_overlap_summary.json"
OUT_PATH = ROOT / "data" / "stats.json"

START_EQUITY = 100.0
CLEAN_LEVERAGE = 30.0
NOTIONAL_CAP = 8000.0
DUST_QTY = 0.0001
PUBLIC_HEARTBEAT_MINUTES = 4


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    except Exception:
        return rows
    return rows


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


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


def performance_windows(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    windows: list[tuple[str, timedelta | None]] = [
        ("24h", timedelta(hours=24)),
        ("7d", timedelta(days=7)),
        ("30d", timedelta(days=30)),
        ("all", None),
    ]
    rows: list[dict[str, Any]] = []
    for label, delta in windows:
        if delta is None:
            bucket = list(trades)
            since = parse_time(bucket[0].get("closedAt") or bucket[0].get("openedAt")) if bucket else datetime.min.replace(tzinfo=timezone.utc)
        else:
            since = now - delta
            bucket = [
                trade for trade in trades
                if parse_time(trade.get("closedAt") or trade.get("openedAt")) >= since
            ]

        pnls = [number(trade.get("pnl")) for trade in bucket]
        returns = [trade_return_pct(trade) for trade in bucket]
        wins = [pnl for pnl in pnls if pnl > 0]
        losses = [pnl for pnl in pnls if pnl < 0]
        slippages = [number(trade.get("slippageBp"), math.nan) for trade in bucket if trade.get("slippageBp") not in ("", None)]
        execution_costs = [
            number(trade.get("executionCostBp"), math.nan)
            for trade in bucket
            if trade.get("executionCostBp") not in ("", None)
        ]
        curve_points, ending_equity = clean_curve(bucket)
        dd_dollar, dd_pct = max_drawdown(curve_points)
        clean_net_pct = round((ending_equity / START_EQUITY - 1.0) * 100.0, 2)
        clean_dd_dollar = round(dd_dollar, 4)
        clean_dd_pct = round(dd_pct, 2)
        rows.append(
            {
                "window": label,
                "since_utc": public_time(since),
                "trade_count": len(bucket),
                "net_pnl": round(sum(pnls), 4),
                "profit_factor": round(profit_factor(pnls), 4),
                "win_rate_pct": round(len(wins) / len(bucket) * 100.0, 2) if bucket else 0.0,
                "avg_trade_pnl": round(avg(pnls), 4),
                "avg_trade_return_pct": round(avg(returns), 5),
                "gross_profit": round(sum(wins), 4),
                "gross_loss": round(sum(losses), 4),
                "avg_slippage_bp": round(avg(slippages), 4),
                "avg_execution_cost_bp": round(avg(execution_costs), 4),
                "clean_leveraged_net_pct": clean_net_pct,
                "clean_leveraged_max_drawdown": clean_dd_dollar,
                "clean_leveraged_max_drawdown_pct": clean_dd_pct,
                "clean_25x_net_pct": clean_net_pct,
                "clean_25x_max_drawdown": clean_dd_dollar,
                "clean_25x_max_drawdown_pct": clean_dd_pct,
            }
        )
    return rows


def compact_trade_stats(label: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    pnls = [number(trade.get("pnl")) for trade in trades]
    returns = [trade_return_pct(trade) for trade in trades]
    wins = [pnl for pnl in pnls if pnl > 0]
    execution_costs = [
        number(trade.get("executionCostBp"), math.nan)
        for trade in trades
        if trade.get("executionCostBp") not in ("", None)
    ]
    return {
        "label": label,
        "count": len(trades),
        "net_pnl": round(sum(pnls), 4),
        "profit_factor": round(profit_factor(pnls), 4),
        "win_rate_pct": round(len(wins) / len(trades) * 100.0, 2) if trades else 0.0,
        "avg_trade_pnl": round(avg(pnls), 4),
        "avg_return_pct": round(avg(returns), 5),
        "avg_execution_cost_bp": round(avg(execution_costs), 4),
    }


def performance_breakdowns(trades: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hour_buckets = [
        ("00-05 UTC", 0, 6),
        ("06-11 UTC", 6, 12),
        ("12-17 UTC", 12, 18),
        ("18-23 UTC", 18, 24),
    ]

    def closed_dt(trade: dict[str, Any]) -> datetime:
        return parse_time(trade.get("closedAt") or trade.get("openedAt"))

    side_rows = []
    for side in sorted({str(trade.get("side", "")).lower() or "unknown" for trade in trades}):
        side_rows.append(compact_trade_stats(side, [trade for trade in trades if str(trade.get("side", "")).lower() == side]))

    reason_rows = []
    for reason in sorted({str(trade.get("exitReason", "")).lower() or "unknown" for trade in trades}):
        bucket = [
            trade for trade in trades
            if (str(trade.get("exitReason", "")).lower() or "unknown") == reason
        ]
        reason_rows.append(compact_trade_stats(reason, bucket))
    reason_rows.sort(key=lambda item: item["count"], reverse=True)

    weekday_rows = []
    for index, label in enumerate(weekdays):
        weekday_rows.append(compact_trade_stats(label, [trade for trade in trades if closed_dt(trade).weekday() == index]))

    hour_rows = []
    for label, low, high in hour_buckets:
        hour_rows.append(compact_trade_stats(label, [trade for trade in trades if low <= closed_dt(trade).hour < high]))

    return {
        "side": side_rows,
        "exit_reason": reason_rows,
        "weekday_utc": weekday_rows,
        "hour_utc": hour_rows,
    }


def risk_hotspots(
    trades: list[dict[str, Any]],
    curve_points: list[dict[str, Any]],
    breakdowns: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    losses = sorted(
        [trade for trade in trades if number(trade.get("pnl")) < 0],
        key=lambda trade: number(trade.get("pnl")),
    )
    gross_loss_abs = abs(sum(number(trade.get("pnl")) for trade in losses))

    def closed_dt(trade: dict[str, Any]) -> datetime:
        return parse_time(trade.get("closedAt") or trade.get("openedAt"))

    def hour_bucket(dt: datetime) -> str:
        hour = dt.hour
        if hour < 6:
            return "00-05 UTC"
        if hour < 12:
            return "06-11 UTC"
        if hour < 18:
            return "12-17 UTC"
        return "18-23 UTC"

    def loss_marker(trade: dict[str, Any]) -> dict[str, Any]:
        dt = closed_dt(trade)
        return {
            "closed_at": public_time(dt),
            "side": str(trade.get("side", "")).lower(),
            "pnl": round(number(trade.get("pnl")), 4),
            "return_pct": round(trade_return_pct(trade), 5),
            "notional": round(abs(number(trade.get("notional"))), 2),
            "hour_bucket": hour_bucket(dt),
            "weekday_utc": dt.strftime("%a"),
            "entry_book_chase_bp": round(number(trade.get("entryBookChaseBp")), 4),
            "slippage_bp": round(number(trade.get("slippageBp")), 4),
            "exit_reason": str(trade.get("exitReason", ""))[:60],
        }

    worst_drawdown = {
        "time": "",
        "drawdown": 0.0,
        "drawdown_pct": 0.0,
        "peak_equity": START_EQUITY,
        "trough_equity": START_EQUITY,
    }
    peak = START_EQUITY
    for point in curve_points:
        equity = number(point.get("equity"), START_EQUITY)
        peak = max(peak, equity)
        drawdown = peak - equity
        drawdown_pct = drawdown / peak * 100.0 if peak else 0.0
        if drawdown > worst_drawdown["drawdown"]:
            worst_drawdown = {
                "time": public_time(point.get("time")),
                "drawdown": round(drawdown, 4),
                "drawdown_pct": round(drawdown_pct, 2),
                "peak_equity": round(peak, 4),
                "trough_equity": round(equity, 4),
            }

    worst_streak = {
        "count": 0,
        "pnl": 0.0,
        "start": "",
        "end": "",
    }
    current_streak: list[dict[str, Any]] = []
    for trade in trades:
        if number(trade.get("pnl")) < 0:
            current_streak.append(trade)
            streak_pnl = sum(number(item.get("pnl")) for item in current_streak)
            if len(current_streak) > int(worst_streak["count"]) or streak_pnl < number(worst_streak["pnl"]):
                worst_streak = {
                    "count": len(current_streak),
                    "pnl": round(streak_pnl, 4),
                    "start": public_time(current_streak[0].get("closedAt") or current_streak[0].get("openedAt")),
                    "end": public_time(current_streak[-1].get("closedAt") or current_streak[-1].get("openedAt")),
                }
        else:
            current_streak = []

    weak_buckets: list[dict[str, Any]] = []
    for group, rows in breakdowns.items():
        for row in rows:
            count = int(number(row.get("count")))
            net_pnl = number(row.get("net_pnl"))
            pf = number(row.get("profit_factor"))
            if count >= 4 and net_pnl < 0 and pf < 1.0:
                weak_buckets.append(
                    {
                        "group": group,
                        "label": row.get("label", ""),
                        "count": count,
                        "net_pnl": round(net_pnl, 4),
                        "profit_factor": round(pf, 4),
                        "win_rate_pct": round(number(row.get("win_rate_pct")), 2),
                    }
                )
    weak_buckets.sort(key=lambda item: item["net_pnl"])

    top_losses = [loss_marker(trade) for trade in losses[:5]]
    top_three_abs = sum(abs(number(trade.get("pnl"))) for trade in losses[:3])
    largest_loss_abs = abs(number(losses[0].get("pnl"))) if losses else 0.0
    return {
        "loss_count": len(losses),
        "gross_loss_abs": round(gross_loss_abs, 4),
        "largest_loss_abs": round(largest_loss_abs, 4),
        "largest_loss_share_pct": round(largest_loss_abs / gross_loss_abs * 100.0, 2) if gross_loss_abs else 0.0,
        "top3_loss_share_pct": round(top_three_abs / gross_loss_abs * 100.0, 2) if gross_loss_abs else 0.0,
        "worst_drawdown": worst_drawdown,
        "worst_loss_streak": worst_streak,
        "weak_buckets": weak_buckets[:6],
        "worst_losses": top_losses,
    }


def time_filter_what_if(trades: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hour_buckets = [
        ("00-05 UTC", 0, 6),
        ("06-11 UTC", 6, 12),
        ("12-17 UTC", 12, 18),
        ("18-23 UTC", 18, 24),
    ]
    base = compact_trade_stats("base", trades)

    def closed_dt(trade: dict[str, Any]) -> datetime:
        return parse_time(trade.get("closedAt") or trade.get("openedAt"))

    def exclusion_row(label: str, removed: list[dict[str, Any]]) -> dict[str, Any]:
        removed_ids = {id(trade) for trade in removed}
        kept = [trade for trade in trades if id(trade) not in removed_ids]
        kept_stats = compact_trade_stats(label, kept)
        removed_stats = compact_trade_stats(label, removed)
        kept_stats.update(
            {
                "removed_count": len(removed),
                "removed_net_pnl": removed_stats["net_pnl"],
                "net_pnl_delta": round(kept_stats["net_pnl"] - base["net_pnl"], 4),
                "profit_factor_delta": round(kept_stats["profit_factor"] - base["profit_factor"], 4),
            }
        )
        return kept_stats

    def candidate_row(group: str, row: dict[str, Any]) -> dict[str, Any]:
        improved = row["net_pnl_delta"] > 0 and row["profit_factor_delta"] > 0
        enough_removed = row["removed_count"] >= 8
        enough_kept = row["count"] >= 30
        enough_total = len(trades) >= 100
        if not improved:
            readiness = "reject"
            reason = "Would not improve both net PnL and PF."
        elif not enough_removed or not enough_kept:
            readiness = "too small"
            reason = "Positive, but removed/kept sample is too small."
        elif not enough_total:
            readiness = "watch only"
            reason = "Positive, but total live sample is under 100 trades."
        else:
            readiness = "candidate"
            reason = "Improves sample with enough live trades to consider testing as a rule."
        score = 0.0
        if improved:
            score = row["net_pnl_delta"] + row["profit_factor_delta"] * 10.0 + row["removed_count"] * 0.1
        return {
            "group": group,
            "label": row["label"],
            "readiness": readiness,
            "reason": reason,
            "score": round(score, 4),
            "kept_count": row["count"],
            "removed_count": row["removed_count"],
            "net_pnl_delta": row["net_pnl_delta"],
            "profit_factor": row["profit_factor"],
            "profit_factor_delta": row["profit_factor_delta"],
        }

    hour_rows = [
        exclusion_row(label, [trade for trade in trades if low <= closed_dt(trade).hour < high])
        for label, low, high in hour_buckets
    ]
    weekday_rows = [
        exclusion_row(label, [trade for trade in trades if closed_dt(trade).weekday() == index])
        for index, label in enumerate(weekdays)
    ]
    hour_rows.sort(key=lambda item: item["net_pnl_delta"], reverse=True)
    weekday_rows.sort(key=lambda item: item["net_pnl_delta"], reverse=True)
    candidates = [
        candidate_row("hour", row) for row in hour_rows
    ] + [
        candidate_row("weekday", row) for row in weekday_rows
    ]
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return {
        "base": base,
        "exclude_hour_utc": hour_rows,
        "exclude_weekday_utc": weekday_rows,
        "candidates": candidates,
    }


def strategy_research_candidate() -> dict[str, Any]:
    lt6_followup = read_json(STRATEGY_LT6_LBE4_FOLLOWUP_PATH, {})
    lt4_overlap = read_json(STRATEGY_LT4_LD2_LIVE_OVERLAP_PATH, {})
    lt6_followup_baseline = lt6_followup.get("baseline") or {}
    lt4_pick = lt6_followup.get("best_candidate") or {}
    if lt4_pick and lt4_pick.get("case") == "long_trail_0.00004_0.00002":
        overlap_safe = bool(lt4_overlap.get("promotion_safe"))
        return {
            "model": "entry_research_atr975_stop220_h07_h10_trail12_short35h15_lbe5_sbe10_lt4_ld2",
            "variant": lt4_pick.get("case") or "",
            "net_pct": round(number(lt4_pick.get("avgspread_net")), 4),
            "profit_factor": round(number(lt4_pick.get("avgspread_pf")), 4),
            "max_drawdown_pct": round(number(lt4_pick.get("avgspread_dd")), 4),
            "trades_per_year": round(number(lt4_pick.get("trades_per_year")), 2),
            "avg_trade_pct": round(number(lt4_pick.get("avgspread_avg_trade_pct")), 5),
            "baseline_net_pct": round(number(lt6_followup_baseline.get("avgspread_net")), 4),
            "baseline_profit_factor": round(number(lt6_followup_baseline.get("avgspread_pf")), 4),
            "baseline_max_drawdown_pct": round(number(lt6_followup_baseline.get("avgspread_dd")), 4),
            "baseline_trades_per_year": round(number(lt6_followup_baseline.get("trades_per_year")), 2),
            "live_overlap_entries": int(number(lt4_overlap.get("common_entries"))),
            "live_overlap_actual_matches": int(number(lt4_overlap.get("actual_overlap_count"))),
            "live_overlap_delta_return_pct_sum": round(number(lt4_overlap.get("actual_overlap_delta_return_pct_sum")), 6),
            "live_overlap_delta_bp_avg": round(number(lt4_overlap.get("actual_overlap_delta_bp_avg")), 4),
            "live_overlap_skipped_count": int(number(lt4_overlap.get("current_only_entries"))),
            "live_overlap_safe": overlap_safe,
            "promotion_safe": overlap_safe,
            "caution": (
                "Promoted candidate: same entries/sizing/guards as LT6/LBE4, but long trailing activates at 0.004% "
                "with 0.002% distance. Follow-up full-period scan improved net/PF/2bp stress PF without increasing "
                "drawdown, and live-overlap was positive."
            ),
        }

    lt8_post = read_json(STRATEGY_LT8_POST_PROMOTION_PATH, {})
    lt6_overlap = read_json(STRATEGY_LT6_LBE4_LIVE_OVERLAP_PATH, {})
    lt8_post_baseline = lt8_post.get("baseline") or {}
    lt6_pick = lt8_post.get("best_candidate") or {}
    if lt6_pick and lt6_pick.get("case") == "lt006_003_lbe004_004":
        overlap_safe = bool(lt6_overlap.get("promotion_safe"))
        return {
            "model": "entry_research_atr975_stop220_h07_h10_trail12_short35h15_lbe5_sbe10_lt6_lbe4",
            "variant": lt6_pick.get("case") or "",
            "net_pct": round(number(lt6_pick.get("avgspread_net")), 4),
            "profit_factor": round(number(lt6_pick.get("avgspread_pf")), 4),
            "max_drawdown_pct": round(number(lt6_pick.get("avgspread_dd")), 4),
            "trades_per_year": round(number(lt6_pick.get("trades_per_year")), 2),
            "avg_trade_pct": round(number(lt6_pick.get("avgspread_avg_trade_pct")), 5),
            "baseline_net_pct": round(number(lt8_post_baseline.get("avgspread_net")), 4),
            "baseline_profit_factor": round(number(lt8_post_baseline.get("avgspread_pf")), 4),
            "baseline_max_drawdown_pct": round(number(lt8_post_baseline.get("avgspread_dd")), 4),
            "baseline_trades_per_year": round(number(lt8_post_baseline.get("trades_per_year")), 2),
            "live_overlap_entries": int(number(lt6_overlap.get("common_entries"))),
            "live_overlap_actual_matches": int(number(lt6_overlap.get("actual_overlap_count"))),
            "live_overlap_delta_return_pct_sum": round(number(lt6_overlap.get("actual_overlap_delta_return_pct_sum")), 6),
            "live_overlap_delta_bp_avg": round(number(lt6_overlap.get("actual_overlap_delta_bp_avg")), 4),
            "live_overlap_skipped_count": int(number(lt6_overlap.get("current_only_entries"))),
            "live_overlap_safe": overlap_safe,
            "promotion_safe": overlap_safe,
            "caution": (
                "Promoted candidate: same entries/sizing/guards as LT8, but long trailing activates at 0.006% "
                "with 0.003% distance and long break-even at 0.004% / 0.004% lock. Full-period Lighter scan "
                "and live-overlap both improved net/PF without increasing drawdown."
            ),
        }

    net_preserving = read_json(STRATEGY_SBE10_NET_PRESERVING_PATH, {})
    lt8_overlap = read_json(STRATEGY_LT8_LIVE_OVERLAP_PATH, {})
    net_preserving_baseline = net_preserving.get("baseline") or {}
    net_preserving_rows = net_preserving.get("top_20") or []
    net_pick = next((row for row in net_preserving_rows if row.get("case") == "long_trail_0.00008_0.00004"), {})
    if net_pick:
        overlap_safe = bool(lt8_overlap.get("promotion_safe"))
        return {
            "model": "entry_research_atr975_stop220_h07_h10_trail12_short35h15_lbe5_sbe10_lt8",
            "variant": net_pick.get("case") or "",
            "net_pct": round(number(net_pick.get("avgspread_net")), 4),
            "profit_factor": round(number(net_pick.get("avgspread_pf")), 4),
            "max_drawdown_pct": round(number(net_pick.get("avgspread_dd")), 4),
            "trades_per_year": round(number(net_pick.get("trades_per_year")), 2),
            "avg_trade_pct": round(number(net_pick.get("avgspread_avg_trade_pct")), 5),
            "baseline_net_pct": round(number(net_preserving_baseline.get("avgspread_net")), 4),
            "baseline_profit_factor": round(number(net_preserving_baseline.get("avgspread_pf")), 4),
            "baseline_max_drawdown_pct": round(number(net_preserving_baseline.get("avgspread_dd")), 4),
            "baseline_trades_per_year": round(number(net_preserving_baseline.get("trades_per_year")), 2),
            "live_overlap_entries": int(number(lt8_overlap.get("common_entries"))),
            "live_overlap_actual_matches": int(number(lt8_overlap.get("actual_overlap_count"))),
            "live_overlap_delta_return_pct_sum": round(number(lt8_overlap.get("actual_overlap_delta_return_pct_sum")), 6),
            "live_overlap_delta_bp_avg": round(number(lt8_overlap.get("actual_overlap_delta_bp_avg")), 4),
            "live_overlap_skipped_count": int(number(lt8_overlap.get("current_only_entries"))),
            "live_overlap_skipped_net_pnl": 0.0,
            "live_overlap_safe": overlap_safe,
            "promotion_safe": overlap_safe,
            "caution": (
                "Promoted candidate: same live entries/sizing/guards as SBE10, but long trailing activates "
                "at 0.008% with 0.004% distance. Full backtest and live-period overlap both improved net/PF "
                "without increasing drawdown."
            ),
        }

    fast_cut = read_json(STRATEGY_SBE10_FAST_CUT_PATH, {})
    fast_cut_baseline = fast_cut.get("baseline") or {}
    fast_cut_rows = fast_cut.get("top_18") or []
    fast_cut_selected = next((row for row in fast_cut_rows if row.get("case") == "short_no_prog_3_0.00005"), {})
    if fast_cut_selected:
        return {
            "model": "entry_research_atr975_stop220_h07_h10_trail12_short35h15_lbe5_sbe10_snp3",
            "variant": fast_cut_selected.get("case") or "",
            "net_pct": round(number(fast_cut_selected.get("avgspread_net")), 4),
            "profit_factor": round(number(fast_cut_selected.get("avgspread_pf")), 4),
            "max_drawdown_pct": round(number(fast_cut_selected.get("avgspread_dd")), 4),
            "trades_per_year": round(number(fast_cut_selected.get("trades_per_year")), 2),
            "avg_trade_pct": round(number(fast_cut_selected.get("avgspread_avg_trade_pct")), 5),
            "baseline_net_pct": round(number(fast_cut_baseline.get("avgspread_net")), 4),
            "baseline_profit_factor": round(number(fast_cut_baseline.get("avgspread_pf")), 4),
            "baseline_max_drawdown_pct": round(number(fast_cut_baseline.get("avgspread_dd")), 4),
            "baseline_trades_per_year": round(number(fast_cut_baseline.get("trades_per_year")), 2),
            "live_overlap_skipped_count": 0,
            "live_overlap_skipped_net_pnl": 0.0,
            "live_overlap_safe": True,
            "promotion_safe": True,
            "caution": (
                "Research candidate only: same entries/sizing/guards, long BE at 0.005%, "
                "short BE at 0.010%, and short no-progress exit after 3 bars without 0.005% favorable move."
            ),
        }

    lbe5_short = read_json(STRATEGY_LBE5_SHORT_EXIT_PATH, {})
    lbe5_baseline = lbe5_short.get("baseline") or {}
    lbe5_rows = lbe5_short.get("top_16") or []
    lbe5_selected = next((row for row in lbe5_rows if row.get("case") == "short_be_0.00010_0.00005"), {})
    if lbe5_selected:
        return {
            "model": "entry_research_atr975_stop220_h07_h10_trail12_short35h15_lbe5_sbe10",
            "variant": lbe5_selected.get("case") or "",
            "net_pct": round(number(lbe5_selected.get("avgspread_net")), 4),
            "profit_factor": round(number(lbe5_selected.get("avgspread_pf")), 4),
            "max_drawdown_pct": round(number(lbe5_selected.get("avgspread_dd")), 4),
            "trades_per_year": round(number(lbe5_selected.get("trades_per_year")), 2),
            "avg_trade_pct": round(number(lbe5_selected.get("avgspread_avg_trade_pct")), 5),
            "baseline_net_pct": round(number(lbe5_baseline.get("avgspread_net")), 4),
            "baseline_profit_factor": round(number(lbe5_baseline.get("avgspread_pf")), 4),
            "baseline_max_drawdown_pct": round(number(lbe5_baseline.get("avgspread_dd")), 4),
            "baseline_trades_per_year": round(number(lbe5_baseline.get("trades_per_year")), 2),
            "live_overlap_skipped_count": 0,
            "live_overlap_skipped_net_pnl": 0.0,
            "live_overlap_safe": True,
            "promotion_safe": True,
            "caution": (
                "Promoted as current live default: same entries/sizing/guards, long BE at 0.005%, "
                "and short BE trigger tightened to 0.010% while keeping the 0.005% lock."
            ),
        }

    be_plateau = read_json(STRATEGY_BE_PLATEAU_PATH, {})
    be_baseline = be_plateau.get("baseline") or {}
    be_rows = be_plateau.get("top_12") or []
    be_selected = next((row for row in be_rows if row.get("case") == "long_be_0.00005_0.00002"), {})
    if be_selected:
        return {
            "model": "entry_research_atr975_stop220_h07_h10_trail12_short35h15_lbe5",
            "variant": be_selected.get("case") or "",
            "net_pct": round(number(be_selected.get("avgspread_net")), 4),
            "profit_factor": round(number(be_selected.get("avgspread_pf")), 4),
            "max_drawdown_pct": round(number(be_selected.get("avgspread_dd")), 4),
            "trades_per_year": round(number(be_selected.get("trades_per_year")), 2),
            "avg_trade_pct": round(number(be_selected.get("avgspread_avg_trade_pct")), 5),
            "baseline_net_pct": round(number(be_baseline.get("avgspread_net")), 4),
            "baseline_profit_factor": round(number(be_baseline.get("avgspread_pf")), 4),
            "baseline_max_drawdown_pct": round(number(be_baseline.get("avgspread_dd")), 4),
            "baseline_trades_per_year": round(number(be_baseline.get("trades_per_year")), 2),
            "live_overlap_skipped_count": 0,
            "live_overlap_skipped_net_pnl": 0.0,
            "live_overlap_safe": True,
            "promotion_safe": True,
            "caution": (
                "Promoted as current live default: same entries/sizing/guards, long break-even trigger "
                "tightened to 0.005% while keeping the existing 0.002% lock."
            ),
        }

    trail12_short35 = read_json(STRATEGY_TRAIL12_SHORT35_PATH, {})
    selected = trail12_short35.get("best") or {}
    baseline = trail12_short35.get("baseline") or {}
    if selected:
        return {
            "model": "entry_research_atr975_stop220_h07_h10_trail12_short35h15",
            "variant": selected.get("candidate") or selected.get("case") or "",
            "net_pct": round(number(selected.get("visible_net_pct")), 4),
            "profit_factor": round(number(selected.get("visible_pf")), 4),
            "max_drawdown_pct": round(number(selected.get("visible_dd_pct")), 4),
            "trades_per_year": round(number(selected.get("trades_per_year")), 2),
            "avg_trade_pct": round(number(selected.get("visible_avg_trade_pct")), 5),
            "baseline_net_pct": round(number(baseline.get("visible_net_pct")), 4),
            "baseline_profit_factor": round(number(baseline.get("visible_pf")), 4),
            "baseline_max_drawdown_pct": round(number(baseline.get("visible_dd_pct")), 4),
            "baseline_trades_per_year": round(number(baseline.get("trades_per_year")), 2),
            "live_overlap_skipped_count": 0,
            "live_overlap_skipped_net_pnl": 0.0,
            "live_overlap_safe": True,
            "promotion_safe": bool(selected.get("realistic_ok", True)),
            "caution": selected.get("note") or "Promoted as the current live default; monitor forward fills before adding another filter.",
        }

    trail18 = read_json(STRATEGY_TRAIL18_PATH, {})
    trail_rows = trail18.get("rows") or []
    if len(trail_rows) >= 2:
        baseline = trail_rows[0] or {}
        selected = trail_rows[1] or {}
        return {
            "model": selected.get("model") or "",
            "variant": selected.get("candidate") or "",
            "net_pct": round(number(selected.get("visible_net_pct")), 4),
            "profit_factor": round(number(selected.get("visible_pf")), 4),
            "max_drawdown_pct": round(number(selected.get("visible_dd_pct")), 4),
            "trades_per_year": round(number(selected.get("trades_per_year")), 2),
            "avg_trade_pct": round(number(selected.get("visible_avg_trade_pct") or selected.get("cost_avg_trade_pct")), 5),
            "baseline_net_pct": round(number(baseline.get("visible_net_pct")), 4),
            "baseline_profit_factor": round(number(baseline.get("visible_pf")), 4),
            "baseline_max_drawdown_pct": round(number(baseline.get("visible_dd_pct")), 4),
            "baseline_trades_per_year": round(number(baseline.get("trades_per_year")), 2),
            "live_overlap_skipped_count": 0,
            "live_overlap_skipped_net_pnl": 0.0,
            "live_overlap_safe": True,
            "promotion_safe": True,
            "caution": "Promoted as the current live default; monitor forward fills before adding another filter.",
        }

    promotion = read_json(STRATEGY_PROMOTION_DECISION_PATH, {})
    selected = promotion.get("selected_safe_candidate") or {}
    baseline_model = promotion.get("baseline_model") or "tight_ret240"
    if selected:
        rows = read_csv_rows(Path(promotion.get("csv") or ""))
        baseline = next((row for row in rows if row.get("model") == baseline_model), {})
        return {
            "model": selected.get("model") or "",
            "variant": selected.get("candidate") or "",
            "net_pct": round(number(selected.get("visible_net_pct")), 4),
            "profit_factor": round(number(selected.get("visible_pf")), 4),
            "max_drawdown_pct": round(number(selected.get("visible_dd_pct")), 4),
            "trades_per_year": round(number(selected.get("trades_per_year")), 2),
            "avg_trade_pct": round(number(selected.get("avg_trade_pct")), 5),
            "baseline_net_pct": round(number(baseline.get("visible_net_pct")), 4),
            "baseline_profit_factor": round(number(baseline.get("visible_pf")), 4),
            "baseline_max_drawdown_pct": round(number(baseline.get("visible_dd_pct")), 4),
            "baseline_trades_per_year": round(number(baseline.get("trades_per_year")), 2),
            "live_overlap_skipped_count": int(number(selected.get("live_overlap_skipped_count"))),
            "live_overlap_skipped_net_pnl": round(number(selected.get("live_overlap_skipped_net_pnl")), 4),
            "live_overlap_safe": bool(selected.get("live_overlap_safe")),
            "promotion_safe": bool(selected.get("promotion_safe")),
            "caution": promotion.get("recommendation") or "Shadow candidate only; live overlap is checked separately before promotion.",
        }

    relaxed = read_json(STRATEGY_RELAXED_PATH, {})
    selected = relaxed.get("selected") or {}
    if selected:
        rows = read_csv_rows(STRATEGY_RELAXED_CSV_PATH)
        baseline = next(
            (
                row for row in rows
                if row.get("model") == "tight_ret240"
                and row.get("exit_variant") == "base_exit"
                and not row.get("atr_cap")
                and row.get("block_long_h16") == "False"
            ),
            {},
        )
        return {
            "model": "relaxed_quality_atr150",
            "variant": (
                f"{selected.get('model', '')}:{selected.get('exit_variant', '')}:"
                f"atr={selected.get('atr_cap', '')}:h16={selected.get('block_long_h16', '')}"
            ),
            "net_pct": round(number(selected.get("visible_net_pct")), 4),
            "profit_factor": round(number(selected.get("visible_pf")), 4),
            "max_drawdown_pct": round(number(selected.get("visible_dd_pct")), 4),
            "trades_per_year": round(number(selected.get("trades_per_year")), 2),
            "avg_trade_pct": round(number(selected.get("avg_trade_pct")), 5),
            "baseline_net_pct": round(number(baseline.get("visible_net_pct")), 4),
            "baseline_profit_factor": round(number(baseline.get("visible_pf")), 4),
            "baseline_max_drawdown_pct": round(number(baseline.get("visible_dd_pct")), 4),
            "baseline_trades_per_year": round(number(baseline.get("trades_per_year")), 2),
            "caution": "Shadow candidate only; live overlap is checked separately before promotion.",
        }

    research = read_json(STRATEGY_RESEARCH_PATH, {})
    selected = research.get("selected_visible_spread") or {}
    baseline = research.get("baseline_visible_spread") or {}
    if not selected or not baseline:
        return {}
    return {
        "model": "entry_research_quality_guard",
        "variant": selected.get("variant") or "",
        "net_pct": round(number(selected.get("net_pct")), 4),
        "profit_factor": round(number(selected.get("profit_factor")), 4),
        "max_drawdown_pct": round(number(selected.get("max_drawdown_pct")), 4),
        "trades_per_year": round(number(selected.get("trades_per_year")), 2),
        "avg_trade_pct": round(number(selected.get("avg_trade_pct")), 5),
        "baseline_net_pct": round(number(baseline.get("net_pct")), 4),
        "baseline_profit_factor": round(number(baseline.get("profit_factor")), 4),
        "baseline_max_drawdown_pct": round(number(baseline.get("max_drawdown_pct")), 4),
        "baseline_trades_per_year": round(number(baseline.get("trades_per_year")), 2),
        "caution": "Research candidate only; shadow-test before using as the live default.",
    }


def strategy_execution_stress() -> dict[str, Any]:
    stress = read_json(STRATEGY_LT4_EXECUTION_STRESS_PATH, {})
    rows = stress.get("scenario_deltas") or []
    if not rows:
        return {}
    base = next((row for row in rows if row.get("scenario") == "base_avgspread"), rows[0])
    harsh = next((row for row in rows if row.get("scenario") == "long_trail_plus_1bp"), rows[-1])
    overlap = stress.get("overlap_delta") or {}
    return {
        "generated_at_utc": stress.get("generated_at_utc") or "",
        "comparison": stress.get("comparison") or "",
        "base_net_delta": round(number(base.get("net_delta")), 4),
        "base_pf_delta": round(number(base.get("pf_delta")), 5),
        "harsh_scenario": harsh.get("scenario") or "",
        "harsh_net_delta": round(number(harsh.get("net_delta")), 4),
        "harsh_pf_delta": round(number(harsh.get("pf_delta")), 5),
        "harsh_two_bp_pf_delta": round(number(harsh.get("two_bp_pf_delta")), 5),
        "overlap_delta_return_pct_sum": round(number(overlap.get("delta_return_pct_sum")), 6),
        "overlap_worsened_entries": int(number(overlap.get("worsened_entries"))),
        "passes": bool(
            number(harsh.get("net_delta")) > 0
            and number(harsh.get("pf_delta")) > 0
            and number(harsh.get("two_bp_pf_delta")) > 0
        ),
        "read": stress.get("read") or "",
    }


def strategy_intrabar_stress() -> dict[str, Any]:
    stress = read_json(STRATEGY_LT4_INTRABAR_STRESS_PATH, {})
    rows = stress.get("rows") or []
    if not rows:
        return {}

    def find(alias: str, mode: str) -> dict[str, Any]:
        return next(
            (
                row
                for row in rows
                if row.get("model_alias") == alias and row.get("mode") == mode
            ),
            {},
        )

    prev_normal = find("lt6_lbe4", "normal")
    curr_normal = find("lt4_ld2", "normal")
    prev_conservative = find("lt6_lbe4", "conservative_samebar")
    curr_conservative = find("lt4_ld2", "conservative_samebar")
    if not curr_conservative or not prev_conservative:
        return {}

    normal_delta = stress.get("normal_lt4_vs_lt6_delta") or {}
    conservative_delta = stress.get("conservative_lt4_vs_lt6_delta") or {}
    current_penalty = number(curr_conservative.get("avgspread_net")) - number(curr_normal.get("avgspread_net"))
    return {
        "generated_at_utc": stress.get("generated_at_utc") or "",
        "normal_net_delta": round(number(curr_normal.get("avgspread_net")) - number(prev_normal.get("avgspread_net")), 4),
        "normal_pf_delta": round(number(curr_normal.get("avgspread_pf")) - number(prev_normal.get("avgspread_pf")), 5),
        "conservative_net_delta": round(number(curr_conservative.get("avgspread_net")) - number(prev_conservative.get("avgspread_net")), 4),
        "conservative_pf_delta": round(number(curr_conservative.get("avgspread_pf")) - number(prev_conservative.get("avgspread_pf")), 5),
        "conservative_dd_delta": round(number(curr_conservative.get("avgspread_dd")) - number(prev_conservative.get("avgspread_dd")), 5),
        "conservative_two_bp_pf_delta": round(number(curr_conservative.get("twobp_pf")) - number(prev_conservative.get("twobp_pf")), 5),
        "current_conservative_net": round(number(curr_conservative.get("avgspread_net")), 4),
        "current_conservative_pf": round(number(curr_conservative.get("avgspread_pf")), 5),
        "current_conservative_dd": round(number(curr_conservative.get("avgspread_dd")), 4),
        "current_conservative_trades_per_year": round(number(curr_conservative.get("trades_per_year")), 2),
        "current_conservative_samebar_trail_exits": int(number(curr_conservative.get("samebar_trail_exits"))),
        "current_conservative_samebar_breakeven_exits": int(number(curr_conservative.get("samebar_breakeven_exits"))),
        "current_net_penalty_vs_normal": round(current_penalty, 4),
        "normal_overlap_worsened_entries": int(number(normal_delta.get("worsened_entries"))),
        "conservative_overlap_worsened_entries": int(number(conservative_delta.get("worsened_entries"))),
        "passes": bool(
            number(curr_conservative.get("avgspread_net")) > number(prev_conservative.get("avgspread_net"))
            and number(curr_conservative.get("avgspread_pf")) > number(prev_conservative.get("avgspread_pf"))
            and number(curr_conservative.get("twobp_pf")) > number(prev_conservative.get("twobp_pf"))
            and number(curr_conservative.get("avgspread_dd")) <= number(prev_conservative.get("avgspread_dd")) + 0.01
        ),
        "read": stress.get("read") or "",
    }


def strategy_shadow_status() -> dict[str, Any]:
    state = read_json(PAPER_STATE_PATH, {})
    shadows = state.get("entry_shadows")
    if not isinstance(shadows, list):
        shadows = []
    selected = None
    for preferred_name in (
        "entry_research_atr975_stop220_h10_trail",
        "entry_research_atr975_stop220_h10_h16_h23_trail20",
        "entry_research_atr975_long_stop220",
        "entry_research_atr975_stop220_h23",
        "entry_research_atr975",
        "entry_research_block_long_h10",
        "entry_research_net_best",
        "entry_research_best",
        "entry_research_h16_atr_guard",
        "relaxed_quality_atr150",
        "entry_research_quality_guard",
    ):
        selected = next(
            (shadow for shadow in shadows if isinstance(shadow, dict) and shadow.get("name") == preferred_name),
            None,
        )
        if selected is not None:
            break
    if selected is None:
        selected = state.get("entry_shadow") if isinstance(state.get("entry_shadow"), dict) else None
    if not selected:
        return {}

    setup = selected.get("setup_diagnostics") or {}
    long_setup = setup.get("long") or {}
    short_setup = setup.get("short") or {}
    current = setup.get("current") or {}
    blockers = list(dict.fromkeys((long_setup.get("blockers") or []) + (short_setup.get("blockers") or [])))
    return {
        "name": selected.get("name") or "",
        "model": selected.get("model") or "",
        "status": selected.get("status") or "",
        "updated_at_utc": public_time(state.get("updated_at_utc")),
        "data_end": public_time(state.get("data_end")),
        "live_model": state.get("model") or "",
        "live_status": state.get("status") or "",
        "live_would_enter_on_latest_candle": bool(selected.get("live_would_enter_on_latest_candle")),
        "shadow_would_enter_on_latest_candle": bool(selected.get("would_enter_on_latest_candle")),
        "live_long_gate": selected.get("live_long_gate") or "",
        "live_short_gate": selected.get("live_short_gate") or "",
        "shadow_long_gate": selected.get("shadow_long_gate") or "",
        "shadow_short_gate": selected.get("shadow_short_gate") or "",
        "primary_blocker": selected.get("shadow_primary_blocker") or setup.get("primary_blocker") or "",
        "blockers": blockers[:6],
        "hour_utc": current.get("hour_utc"),
        "rsi5": round(number(current.get("rsi5")), 4),
        "atr_pct": round(number(current.get("atr_pct")), 8),
    }


def strategy_shadow_activity() -> dict[str, Any]:
    rows = read_jsonl(FREQTRADE_ROOT / "user_data" / "live_state" / "lighter_entry_shadow_journal.jsonl")
    if not rows:
        return {"total_events": 0, "models": [], "recent_events": []}

    rows = sorted(rows, key=lambda row: parse_time(row.get("logged_at_utc")))
    models: list[dict[str, Any]] = []
    for name in sorted({str(row.get("shadow_name") or "unknown") for row in rows}):
        scoped = [row for row in rows if str(row.get("shadow_name") or "unknown") == name]
        divergence = [
            row for row in scoped
            if bool(row.get("live_would_enter_on_latest_candle")) != bool(row.get("shadow_would_enter_on_latest_candle"))
        ]
        models.append(
            {
                "name": name,
                "model": scoped[-1].get("shadow_model") or "",
                "events": len(scoped),
                "divergences": len(divergence),
                "both_would_enter": len([row for row in scoped if row.get("status") == "both_would_enter"]),
                "shadow_only": len([row for row in scoped if row.get("status") == "shadow_would_enter"]),
                "live_only": len([row for row in scoped if row.get("status") == "live_only_signal"]),
                "by_status": count_by(scoped, "status"),
                "latest_event_utc": public_time(scoped[-1].get("logged_at_utc")),
            }
        )

    recent_events = []
    for row in reversed(rows[-8:]):
        recent_events.append(
            {
                "logged_at_utc": public_time(row.get("logged_at_utc")),
                "data_end": public_time(row.get("data_end")),
                "shadow_name": row.get("shadow_name") or "",
                "status": row.get("status") or "",
                "closest_side": row.get("closest_side") or "",
                "primary_blocker": row.get("shadow_primary_blocker") or "",
                "rsi5": round(number(row.get("rsi5")), 4),
                "range_pct": round(number(row.get("range_pct")), 8),
                "relvol_median_1440": round(number(row.get("relvol_median_1440")), 4),
                "ret240_pct": round(number(row.get("ret240_pct")), 4),
            }
        )

    return {
        "total_events": len(rows),
        "since_utc": public_time(rows[0].get("logged_at_utc")),
        "latest_event_utc": public_time(rows[-1].get("logged_at_utc")),
        "models": models,
        "recent_events": recent_events,
    }


def strategy_overlap_status() -> dict[str, Any]:
    summary = read_json(STRATEGY_OVERLAP_PATH, {})
    if not summary:
        return {}

    def compact(name: str) -> dict[str, Any]:
        item = summary.get(name) or {}
        if not isinstance(item, dict):
            return {}
        return {
            "count": int(number(item.get("count"))),
            "net_pnl": round(number(item.get("net_pnl")), 4),
            "profit_factor": round(number(item.get("profit_factor")), 4),
            "win_rate_pct": round(number(item.get("win_rate_pct")), 2),
            "avg_pnl": round(number(item.get("avg_pnl")), 4),
            "avg_return_pct": round(number(item.get("avg_return_pct")), 5),
        }

    return {
        "generated_at_utc": public_time(summary.get("generated_at_utc")),
        "total_public_bot_trades": int(number(summary.get("total_public_bot_trades"))),
        "current_live_matched": compact("current_live_matched"),
        "entry_research_best_skipped_current_live": compact("entry_research_best_skipped_current_live"),
        "entry_research_net_best_skipped_current_live": compact("entry_research_net_best_skipped_current_live"),
        "entry_research_atr975_skipped_current_live": compact("entry_research_atr975_skipped_current_live"),
        "entry_research_atr975_long_stop220_skipped_current_live": compact(
            "entry_research_atr975_long_stop220_skipped_current_live"
        ),
        "entry_research_atr975_stop220_h10_trail_skipped_current_live": compact(
            "entry_research_atr975_stop220_h10_trail_skipped_current_live"
        ),
        "entry_research_atr975_stop220_h10_h16_h23_trail20_skipped_current_live": compact(
            "entry_research_atr975_stop220_h10_h16_h23_trail20_skipped_current_live"
        ),
        "entry_research_atr975_stop220_h23_skipped_current_live": compact(
            "entry_research_atr975_stop220_h23_skipped_current_live"
        ),
        "entry_research_block_long_h10_skipped_current_live": compact(
            "entry_research_block_long_h10_skipped_current_live"
        ),
        "quality_guard_skipped_current_live": compact("quality_guard_skipped_current_live"),
        "h16_atr_guard_skipped_current_live": compact("h16_atr_guard_skipped_current_live"),
        "relaxed_quality_skipped_current_live": compact("relaxed_quality_skipped_current_live"),
        "note": "Overlap uses existing live trades only and is a promotion warning, not proof.",
    }


def decision_queue(
    trades: list[dict[str, Any]],
    time_filter: dict[str, Any],
    strategy_research: dict[str, Any],
    strategy_shadow: dict[str, Any],
    shadow_activity: dict[str, Any],
    strategy_overlap: dict[str, Any],
    current_guard: dict[str, Any],
    expected: dict[str, Any],
    windows: list[dict[str, Any]],
    execution_stress: dict[str, Any],
    intrabar_stress: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(topic: str, status: str, evidence: str, next_step: str, priority: str = "watch") -> None:
        rows.append(
            {
                "topic": topic,
                "status": status,
                "priority": priority,
                "evidence": evidence,
                "next_step": next_step,
            }
        )

    candidates = time_filter.get("candidates") or []
    top_filter = candidates[0] if candidates else {}
    if top_filter:
        missing_total = max(0, 100 - len(trades))
        readiness = str(top_filter.get("readiness", "watch"))
        label = f"{top_filter.get('group', '--')} {top_filter.get('label', '--')}"
        evidence = (
            f"Net delta ${number(top_filter.get('net_pnl_delta')):.2f}, "
            f"PF delta {number(top_filter.get('profit_factor_delta')):.2f}, "
            f"removed {int(number(top_filter.get('removed_count')))} trades."
        )
        if readiness == "candidate":
            next_step = "Test this as a strategy rule before enabling it live."
            priority = "candidate"
        elif readiness == "watch only":
            next_step = f"Collect {missing_total} more public trades and require the edge to persist."
            priority = "watch"
        elif readiness == "too small":
            next_step = "Collect more removed/kept samples before trusting this bucket."
            priority = "watch"
        else:
            next_step = "Do not use this as a filter."
            priority = "reject"
        add(f"Time filter: {label}", readiness, evidence, next_step, priority)

    if strategy_research:
        pf = number(strategy_research.get("profit_factor"))
        base_pf = number(strategy_research.get("baseline_profit_factor"))
        dd = number(strategy_research.get("max_drawdown_pct"))
        base_dd = number(strategy_research.get("baseline_max_drawdown_pct"))
        net = number(strategy_research.get("net_pct"))
        base_net = number(strategy_research.get("baseline_net_pct"))
        trades_year = number(strategy_research.get("trades_per_year"))
        model_name = strategy_research.get("model") or "strategy candidate"
        live_model = ((expected.get("live_status") or {}).get("monitor_model") or expected.get("model") or "")
        evidence = (
            f"PF {pf:.2f} vs {base_pf:.2f}, DD {dd:.2f}% vs {base_dd:.2f}%, "
            f"net {net:.2f}% vs {base_net:.2f}%, {trades_year:.0f} trades/year."
        )
        overlap_key = {
            "entry_research_best": "entry_research_best_skipped_current_live",
            "entry_research_net_best": "entry_research_net_best_skipped_current_live",
            "entry_research_atr975": "entry_research_atr975_skipped_current_live",
            "entry_research_atr975_long_stop220": "entry_research_atr975_long_stop220_skipped_current_live",
            "entry_research_atr975_stop220_h10_trail": "entry_research_atr975_stop220_h10_trail_skipped_current_live",
            "entry_research_atr975_stop220_h10_h16_h23_trail20": "entry_research_atr975_stop220_h10_h16_h23_trail20_skipped_current_live",
            "entry_research_atr975_stop220_h23": "entry_research_atr975_stop220_h23_skipped_current_live",
            "entry_research_block_long_h10": "entry_research_block_long_h10_skipped_current_live",
            "entry_research_h16_atr_guard": "h16_atr_guard_skipped_current_live",
            "entry_research_quality_guard": "quality_guard_skipped_current_live",
            "relaxed_quality_atr150": "relaxed_quality_skipped_current_live",
        }.get(str(model_name), "")
        overlap = strategy_overlap.get(overlap_key) if overlap_key else {}
        if overlap:
            evidence += (
                f" Live overlap: would have skipped {int(number(overlap.get('count')))} current-live "
                f"matched trades totaling ${number(overlap.get('net_pnl')):.2f}."
            )
        overlap_net = number(overlap.get("net_pnl")) if overlap else number(strategy_research.get("live_overlap_skipped_net_pnl"))
        if str(live_model) == str(model_name):
            add(
                f"Active strategy: {model_name}",
                "live",
                evidence,
                "Already running live; keep monitoring fills, slippage, and recent PF before adding another filter.",
                "ok",
            )
        else:
            promotion_safe = bool(strategy_research.get("promotion_safe"))
            if not promotion_safe:
                next_step = "Keep as a research/watch candidate until live-overlap exit checking is finished."
                priority = "watch"
            else:
                next_step = (
                    "Shadow-test as the safest current improvement; it has not skipped net-positive current-live overlap trades."
                    if overlap_net <= 0
                    else "Keep shadow-testing until live overlap stops skipping net-positive current trades."
                )
                priority = "watch" if overlap_net > 0 else "candidate"
            add(
                f"Strategy candidate: {model_name}",
                "research candidate",
                evidence,
                next_step,
                priority,
            )

    if execution_stress:
        status = "passed" if execution_stress.get("passes") else "watch"
        priority = "ok" if execution_stress.get("passes") else "watch"
        evidence = (
            f"Base net delta {number(execution_stress.get('base_net_delta')):.2f}%, "
            f"base PF delta {number(execution_stress.get('base_pf_delta')):.3f}; "
            f"harsh trail +1bp net delta {number(execution_stress.get('harsh_net_delta')):.2f}%, "
            f"PF delta {number(execution_stress.get('harsh_pf_delta')):.3f}."
        )
        next_step = (
            "Keep LT4 live, but verify real fills do not erase the tiny-trail edge."
            if execution_stress.get("passes")
            else "Consider reverting to the prior model if live fills worsen."
        )
        add("Tiny-trail execution stress", status, evidence, next_step, priority)

    if intrabar_stress:
        status = "passed" if intrabar_stress.get("passes") else "watch"
        priority = "ok" if intrabar_stress.get("passes") else "watch"
        evidence = (
            f"Pessimistic same-candle trail: net delta {number(intrabar_stress.get('conservative_net_delta')):.2f}%, "
            f"PF delta {number(intrabar_stress.get('conservative_pf_delta')):.3f}, "
            f"DD delta {number(intrabar_stress.get('conservative_dd_delta')):.3f}%. "
            f"Current conservative PF {number(intrabar_stress.get('current_conservative_pf')):.2f}."
        )
        next_step = (
            "Keep LT4 live; same-candle trail pessimism still leaves it ahead of LT6."
            if intrabar_stress.get("passes")
            else "Re-check whether LT4 is too sensitive to intrabar assumptions before promoting further trail tightening."
        )
        add("Intrabar trail realism check", status, evidence, next_step, priority)

    if strategy_shadow:
        status = str(strategy_shadow.get("status") or "unknown")
        live_ready = bool(strategy_shadow.get("live_would_enter_on_latest_candle"))
        shadow_ready = bool(strategy_shadow.get("shadow_would_enter_on_latest_candle"))
        blocker = strategy_shadow.get("primary_blocker") or "none"
        models = shadow_activity.get("models") if isinstance(shadow_activity, dict) else []
        selected_activity = next(
            (item for item in models or [] if item.get("name") == strategy_shadow.get("name")),
            {},
        )
        history = (
            f"; history {int(number(selected_activity.get('events')))} events, "
            f"{int(number(selected_activity.get('divergences')))} divergences"
            if selected_activity
            else "; history collecting"
        )
        evidence = (
            f"{status}; live L {strategy_shadow.get('live_long_gate', '--')} / S "
            f"{strategy_shadow.get('live_short_gate', '--')} vs shadow L "
            f"{strategy_shadow.get('shadow_long_gate', '--')} / S "
            f"{strategy_shadow.get('shadow_short_gate', '--')}; blocker {blocker}{history}."
        )
        priority = "candidate" if live_ready != shadow_ready else "watch"
        add(
            f"Strategy shadow: {strategy_shadow.get('name') or 'candidate'}",
            "diverged" if live_ready != shadow_ready else "tracking",
            evidence,
            "Compare shadow divergences with real fills before switching live.",
            priority,
        )

    guard_records = int(number(current_guard.get("entry_records")))
    guard_version = current_guard.get("version") or "current guard"
    if guard_version:
        if guard_records < 20:
            add(
                "Entry guard",
                "collecting",
                f"{guard_records} signals since {guard_version}.",
                f"Need {20 - guard_records} more post-guard signals before changing guard thresholds.",
                "watch",
            )
        else:
            add(
                "Entry guard",
                "review",
                f"{guard_records} signals, {current_guard.get('blocked_entries', 0)} blocked.",
                "Compare current-guard PF/drawdown before loosening or tightening.",
                "watch",
            )

    missed = int(number(expected.get("missing_expected_entries")))
    unexpected = int(number(expected.get("unexpected_live_entries")))
    if missed or unexpected:
        add(
            "Model/live match",
            "review now",
            f"{missed} missed, {unexpected} unexpected.",
            "Inspect model-match records before trusting new optimization ideas.",
            "urgent",
        )
    else:
        add(
            "Model/live match",
            "healthy",
            "0 missed and 0 unexpected live entries in latest model-match report.",
            "Keep monitoring.",
            "ok",
        )

    week = next((item for item in windows if item.get("window") == "7d"), {})
    full = next((item for item in windows if item.get("window") == "all"), {})
    if week:
        week_pf = number(week.get("profit_factor"))
        full_pf = number(full.get("profit_factor"))
        if week.get("trade_count", 0) and full_pf and week_pf >= full_pf:
            add(
                "Recent performance",
                "healthy",
                f"7d PF {week_pf:.2f} vs all PF {full_pf:.2f}.",
                "No recent-performance downgrade needed.",
                "ok",
            )
        else:
            add(
                "Recent performance",
                "watch",
                f"7d PF {week_pf:.2f} vs all PF {full_pf:.2f}.",
                "Watch whether recent PF keeps lagging.",
                "watch",
            )

    return rows


def bucket_stats(
    trades: list[dict[str, Any]],
    field: str,
    buckets: list[tuple[str, float, float]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, low, high in buckets:
        bucket = [
            trade
            for trade in trades
            if trade.get(field) not in ("", None)
            and low <= number(trade.get(field)) < high
        ]
        pnls = [number(trade.get("pnl")) for trade in bucket]
        wins = [pnl for pnl in pnls if pnl > 0]
        rows.append(
            {
                "label": label,
                "count": len(bucket),
                "net_pnl": round(sum(pnls), 4),
                "profit_factor": round(profit_factor(pnls), 4),
                "win_rate_pct": round(len(wins) / len(bucket) * 100.0, 2) if bucket else 0.0,
                "avg_trade_pnl": round(avg(pnls), 4),
                "avg_value": round(avg([number(trade.get(field)) for trade in bucket]), 4),
            }
        )
    return rows


def entry_chase_what_if(trades: list[dict[str, Any]], thresholds: list[float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for threshold in thresholds:
        kept = [
            trade
            for trade in trades
            if trade.get("entryBookChaseBp") in ("", None)
            or number(trade.get("entryBookChaseBp")) <= threshold
        ]
        blocked = [
            trade
            for trade in trades
            if trade.get("entryBookChaseBp") not in ("", None)
            and number(trade.get("entryBookChaseBp")) > threshold
        ]
        kept_pnls = [number(trade.get("pnl")) for trade in kept]
        blocked_pnls = [number(trade.get("pnl")) for trade in blocked]
        rows.append(
            {
                "threshold_bp": threshold,
                "kept_count": len(kept),
                "blocked_count": len(blocked),
                "kept_net_pnl": round(sum(kept_pnls), 4),
                "kept_profit_factor": round(profit_factor(kept_pnls), 4),
                "blocked_net_pnl": round(sum(blocked_pnls), 4),
            }
        )
    return rows


def is_entry_record(record: dict[str, Any]) -> bool:
    return str(record.get("effect", "")).startswith("open_")


def is_blocked_record(record: dict[str, Any]) -> bool:
    return str(record.get("mode", "")).lower() == "live_blocked"


def entry_chase_from_record(record: dict[str, Any]) -> float:
    snapshot = record.get("orderbook_snapshot") or {}
    return number(snapshot.get("entry_book_chase_bp"), math.nan)


def guard_activity(ledger_rows: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    windows = [
        ("24h", now - timedelta(hours=24)),
        ("7d", now - timedelta(days=7)),
        ("all", datetime.min.replace(tzinfo=timezone.utc)),
    ]
    entry_rows = [row for row in ledger_rows if is_entry_record(row)]
    blocked_rows = [row for row in entry_rows if is_blocked_record(row)]
    by_window: list[dict[str, Any]] = []

    for label, start in windows:
        scoped_entries = [row for row in entry_rows if parse_time(row.get("checked_at_utc")) >= start]
        scoped_blocked = [row for row in blocked_rows if parse_time(row.get("checked_at_utc")) >= start]
        chase_values = [entry_chase_from_record(row) for row in scoped_blocked]
        chase_values = [value for value in chase_values if not math.isnan(value)]
        by_window.append(
            {
                "window": label,
                "entry_records": len(scoped_entries),
                "sent_entries": len([row for row in scoped_entries if str(row.get("mode", "")).lower() == "live"]),
                "blocked_entries": len(scoped_blocked),
                "block_rate_pct": round(len(scoped_blocked) / len(scoped_entries) * 100.0, 2) if scoped_entries else 0.0,
                "avg_block_chase_bp": round(avg(chase_values), 4),
                "max_block_chase_bp": round(max(chase_values), 4) if chase_values else 0.0,
            }
        )

    latest_block = max(blocked_rows, key=lambda row: parse_time(row.get("checked_at_utc")), default={})
    latest_snapshot = latest_block.get("orderbook_snapshot") or {}
    latest_reasons = (latest_block.get("result") or {}).get("reasons") or []
    return {
        "windows": by_window,
        "latest_block": {
            "time": public_time(latest_block.get("checked_at_utc")),
            "effect": latest_block.get("effect", ""),
            "book_chase_bp": round(number(latest_snapshot.get("entry_book_chase_bp")), 4),
            "spread_bp": round(number(latest_snapshot.get("spread_bp")), 4),
            "reason": str(latest_reasons[0])[:160] if latest_reasons else "",
        }
        if latest_block
        else {},
    }


def current_guard_stats(
    trades: list[dict[str, Any]],
    ledger_rows: list[dict[str, Any]],
    order_config: dict[str, Any],
) -> dict[str, Any]:
    effective_at = order_config.get("entry_preflight_guard_effective_at_utc") or ""
    effective_dt = parse_time(effective_at)
    if effective_dt.year == 1:
        return {}

    entry_rows = [
        row
        for row in ledger_rows
        if is_entry_record(row) and parse_time(row.get("checked_at_utc")) >= effective_dt
    ]
    blocked_rows = [row for row in entry_rows if is_blocked_record(row)]
    sent_rows = [row for row in entry_rows if str(row.get("mode", "")).lower() == "live"]
    closed_trades = [
        trade
        for trade in trades
        if parse_time(trade.get("openedAt")) >= effective_dt
    ]
    pnls = [number(trade.get("pnl")) for trade in closed_trades]
    chase_values = [
        number(trade.get("entryBookChaseBp"), math.nan)
        for trade in closed_trades
        if trade.get("entryBookChaseBp") not in ("", None)
    ]
    slippage_values = [
        number(trade.get("slippageBp"), math.nan)
        for trade in closed_trades
        if trade.get("slippageBp") not in ("", None)
    ]
    blocked_chase_values = [entry_chase_from_record(row) for row in blocked_rows]
    blocked_chase_values = [value for value in blocked_chase_values if not math.isnan(value)]

    return {
        "version": order_config.get("entry_preflight_guard_version", ""),
        "effective_at_utc": public_time(effective_at),
        "entry_records": len(entry_rows),
        "sent_entries": len(sent_rows),
        "blocked_entries": len(blocked_rows),
        "block_rate_pct": round(len(blocked_rows) / len(entry_rows) * 100.0, 2) if entry_rows else 0.0,
        "closed_trades": len(closed_trades),
        "net_pnl": round(sum(pnls), 4),
        "profit_factor": round(profit_factor(pnls), 4),
        "avg_trade_pnl": round(avg(pnls), 4),
        "avg_entry_book_chase_bp": round(avg(chase_values), 4),
        "avg_slippage_bp": round(avg(slippage_values), 4),
        "avg_block_chase_bp": round(avg(blocked_chase_values), 4),
        "max_block_chase_bp": round(max(blocked_chase_values), 4) if blocked_chase_values else 0.0,
    }


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
        "actual_unique_trades",
        "actual_duplicate_trade_links",
        "actual_pnl_sum",
        "actual_return_pct_sum",
        "actual_return_profit_factor",
        "actual_pnl_profit_factor",
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
    live = comparable.get("live_status", {})
    live.pop("monitor_checked_at_utc", None)
    live.pop("watchdog_checked_at_utc", None)
    live.pop("monitor_cycle", None)
    model = comparable.get("model_match", {})
    model.pop("generated_at_utc", None)
    model.pop("until_utc", None)
    for window in comparable.get("performance_windows", []):
        if isinstance(window, dict):
            window.pop("since_utc", None)
            window.pop("until_utc", None)
    return comparable


def main() -> None:
    tracker = read_json(TRACKER_PATH, {})
    account = read_json(ACCOUNT_PATH, {})
    heartbeat = read_json(HEARTBEAT_PATH, {})
    watchdog = read_json(WATCHDOG_PATH, {})
    expected = read_json(EXPECTED_PATH, {})
    order_config = read_json(ORDER_CONFIG_PATH, {})
    ledger_rows = read_jsonl(LEDGER_PATH)

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
    execution_quality = {
        "slippage_buckets": bucket_stats(
            published_trades,
            "slippageBp",
            [
                ("favorable <= -2", -999.0, -2.0),
                ("favorable -2 to 0", -2.0, 0.0),
                ("mild 0 to 1", 0.0, 1.0),
                ("adverse 1 to 2", 1.0, 2.0),
                ("adverse 2 to 5", 2.0, 5.0),
                ("bad > 5", 5.0, 999.0),
            ],
        ),
        "entry_book_chase_buckets": bucket_stats(
            published_trades,
            "entryBookChaseBp",
            [
                ("favorable < 0", -999.0, 0.0),
                ("calm 0 to 2.5", 0.0, 2.5),
                ("watch 2.5 to 3.5", 2.5, 3.5),
                ("blocked zone > 3.5", 3.5, 999.0),
            ],
        ),
        "entry_book_chase_what_if": entry_chase_what_if(
            published_trades,
            [2.5, 3.0, 3.5, 4.0, 5.0],
        ),
    }

    curve_points, ending_equity = clean_curve(published_trades)
    dd_dollar, dd_pct = max_drawdown(curve_points)
    performance_window_rows = performance_windows(published_trades)
    performance_breakdown_rows = performance_breakdowns(published_trades)
    risk_hotspot_rows = risk_hotspots(published_trades, curve_points, performance_breakdown_rows)
    time_filter_rows = time_filter_what_if(published_trades)
    strategy_research = strategy_research_candidate()
    execution_stress = strategy_execution_stress()
    intrabar_stress = strategy_intrabar_stress()
    strategy_shadow = strategy_shadow_status()
    shadow_activity = strategy_shadow_activity()
    strategy_overlap = strategy_overlap_status()

    latest_account = account.get("account") or tracker.get("account_status") or {}
    position = account.get("btc_position") or tracker.get("bot_open_position") or {}
    live_status = tracker.get("live_status") or {}
    available_balance = number(latest_account.get("available_balance"))
    target_leverage = number(order_config.get("target_leverage"))
    max_notional = number(order_config.get("max_notional_usdc"))
    desired_notional = available_balance * target_leverage if target_leverage > 0 else 0.0
    intended_notional = min(desired_notional, max_notional) if max_notional > 0 else desired_notional
    watchdog_stage = str(watchdog.get("stage") or "")
    watchdog_disabled_stages = {"check_only", "watchdog_stopped"}
    watchdog_intentionally_disabled = not watchdog or watchdog_stage in watchdog_disabled_stages
    watchdog_running = bool(watchdog.get("ok") is True and not watchdog_intentionally_disabled)
    watchdog_checked_at = public_time(watchdog.get("checked_at_utc")) if watchdog_running else ""

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
    current_guard = current_guard_stats(published_trades, ledger_rows, order_config)

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
        "performance_windows": performance_window_rows,
        "performance_breakdowns": performance_breakdown_rows,
        "risk_hotspots": risk_hotspot_rows,
        "time_filter_what_if": time_filter_rows,
        "strategy_shadow": strategy_shadow,
        "strategy_shadow_activity": shadow_activity,
        "strategy_overlap": strategy_overlap,
        "promotion_candidate": strategy_research,
        "execution_stress": execution_stress,
        "intrabar_stress": intrabar_stress,
        "decision_queue": decision_queue(
            published_trades,
            time_filter_rows,
            strategy_research,
            strategy_shadow,
            shadow_activity,
            strategy_overlap,
            current_guard,
            expected,
            performance_window_rows,
            execution_stress,
            intrabar_stress,
        ),
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
            "watchdog_ok": watchdog_running,
            "watchdog_enabled": not watchdog_intentionally_disabled,
            "watchdog_intentionally_disabled": watchdog_intentionally_disabled,
            "monitor_checked_at_utc": public_time(heartbeat.get("checked_at_utc")),
            "watchdog_checked_at_utc": watchdog_checked_at,
            "monitor_cycle": int(number(heartbeat.get("cycle"))),
            "live_enabled": bool((account.get("secret_summary") or {}).get("live_enabled") or live_status.get("live_enabled")),
            "paper_status": live_status.get("paper_status") or expected.get("current_paper_status") or "",
            "paper_action": live_status.get("paper_action") or expected.get("current_paper_action") or "",
            "position_side": position.get("side", "flat"),
            "position_btc_abs": number(position.get("position_btc_abs")),
            "available_balance": available_balance,
            "total_asset_value": number(latest_account.get("total_asset_value")),
            "pending_order_count": int(number(latest_account.get("pending_order_count"))),
        },
        "model_match": compact_expected(expected),
        "execution_guard": {
            "sizing_mode": order_config.get("sizing_mode", ""),
            "entry_preflight_guard_version": order_config.get("entry_preflight_guard_version", ""),
            "entry_preflight_guard_effective_at_utc": order_config.get("entry_preflight_guard_effective_at_utc", ""),
            "target_leverage": target_leverage,
            "max_notional_usdc": max_notional,
            "desired_notional_usdc": round(desired_notional, 4),
            "intended_entry_notional_usdc": round(intended_notional, 4),
            "notional_cap_active": bool(max_notional > 0 and desired_notional > max_notional),
            "entry_max_slippage_bp": number(order_config.get("entry_max_slippage_bp")),
            "entry_preflight_max_book_chase_bp": number(order_config.get("entry_preflight_max_book_chase_bp")),
            "entry_preflight_candidate_book_chase_bp": number(order_config.get("entry_preflight_candidate_book_chase_bp")),
            "exit_max_slippage_bp": number(order_config.get("exit_max_slippage_bp")),
            "emergency_exit_slippage_bp": number(order_config.get("emergency_exit_slippage_bp")),
            "max_live_loss_bp": number(order_config.get("max_live_loss_bp")),
            "max_live_loss_account_pct": number(order_config.get("max_live_loss_account_pct")),
        },
        "execution_quality": execution_quality,
        "guard_activity": guard_activity(ledger_rows),
        "current_guard_stats": current_guard,
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
        f"clean_{CLEAN_LEVERAGE:.0f}x={payload['clean_curve']['net_pct']:.2f}%"
    )


if __name__ == "__main__":
    main()
