"""
semantic_validation/rules/cross_tool_rules.py

Explicit cross-tool consistency rules (L9).

Validates consistency across multiple tool calls in the execution history
(accessed through context.history).

RESEARCH CONSTRAINT:
    - Never uses oracle recovery paths or expected results.
    - Only inspects prior steps recorded in context.history.
    - All rules explicitly declare rule_id, participating tools, and rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class CrossToolRule:
    rule_id: str
    target_tool: str
    description: str
    validator: Callable[[str, Dict[str, Any], Dict[str, Any], Any], Tuple[bool, str]]
    source: str = "EXPLICIT_PROJECT_RULE"
    rationale: str = ""

    def check(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        context: Any,
    ) -> Tuple[bool, str]:
        return self.validator(tool_name, arguments, result, context)


def _validate_hotel_booking_consistency(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Dict[str, Any],
    context: Any,
) -> Tuple[bool, str]:
    if not context or not hasattr(context, "history"):
        return True, ""

    booking_hotel_id = arguments.get("hotel_id")
    if not booking_hotel_id:
        return True, ""

    # Look for prior get_hotel_info / search_hotels outputs in history
    for record in context.history:
        prev_tool = getattr(record, "tool_name", "") or (
            record.get("tool_name", "") if isinstance(record, dict) else ""
        )
        if "hotel" in prev_tool and "search" in prev_tool:
            prev_res = getattr(record, "output", {}) or (
                record.get("output", {}) if isinstance(record, dict) else {}
            )
            # If search returned specific valid hotel_ids, ensure booking_hotel_id was found
            available_ids = prev_res.get("available_hotel_ids") or prev_res.get("hotel_ids")
            if isinstance(available_ids, list) and available_ids:
                if booking_hotel_id not in available_ids:
                    return False, (
                        f"Booked hotel_id '{booking_hotel_id}' was not in prior available "
                        f"hotel list: {available_ids}"
                    )
    return True, ""


CROSS_TOOL_RULES: List[CrossToolRule] = [
    CrossToolRule(
        rule_id="CTR-001",
        target_tool="book_hotel",
        description="Booked hotel must match previously queried available hotel IDs",
        validator=_validate_hotel_booking_consistency,
        source="EXPLICIT_PROJECT_RULE",
        rationale="Agent should book a hotel that was confirmed available in prior search step",
    ),
]


def get_cross_tool_rules_for_tool(tool_name: str) -> List[CrossToolRule]:
    return [r for r in CROSS_TOOL_RULES if r.target_tool == tool_name or r.target_tool == "*"]
