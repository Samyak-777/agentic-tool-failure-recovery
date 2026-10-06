"""
semantic_validation/rules/cross_field_rules.py

Explicit cross-field consistency rules (L7).

Rules define logical invariant relationships between multiple fields within the
SAME tool output.

RESEARCH CONSTRAINT:
    Every rule must state:
        - rule_id (CFR-xxx)
        - tool_names (target tools or ["*"])
        - fields_involved (list of field names)
        - relationship description
        - source category and rationale
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class CrossFieldRule:
    rule_id: str
    tool_names: List[str]
    fields_involved: List[str]
    description: str
    validator: Callable[[Dict[str, Any]], Tuple[bool, str]]
    source: str = "EXPLICIT_PROJECT_RULE"
    rationale: str = ""

    def applies_to(self, tool_name: str, result: Dict[str, Any]) -> bool:
        if "*" not in self.tool_names and tool_name not in self.tool_names:
            return False
        # All involved fields must be present in output to check this rule
        return all(f in result for f in self.fields_involved)

    def check(self, result: Dict[str, Any]) -> Tuple[bool, str]:
        return self.validator(result)


def _validate_free_slots_le_total(res: Dict[str, Any]) -> Tuple[bool, str]:
    free_slots = res.get("free_slots")
    total_slots = res.get("total_slots")
    if not isinstance(total_slots, (int, float)):
        return True, ""
    count_free = len(free_slots) if isinstance(free_slots, list) else 0
    if count_free > total_slots:
        return False, (
            f"Count of free_slots ({count_free}) exceeds total_slots ({total_slots})"
        )
    return True, ""


def _validate_start_before_end(res: Dict[str, Any]) -> Tuple[bool, str]:
    start = res.get("start_time")
    end = res.get("end_time")
    if not start or not end:
        return True, ""
    try:
        # Compare strings or numbers directly
        if str(start) >= str(end):
            return False, f"start_time ('{start}') must precede end_time ('{end}')"
    except Exception:
        pass
    return True, ""


def _validate_checkin_before_checkout(res: Dict[str, Any]) -> Tuple[bool, str]:
    cin = res.get("check_in") or res.get("checkin_date")
    cout = res.get("check_out") or res.get("checkout_date")
    if not cin or not cout:
        return True, ""
    try:
        if str(cin) >= str(cout):
            return False, f"check_in date ('{cin}') must precede check_out date ('{cout}')"
    except Exception:
        pass
    return True, ""


def _validate_departure_before_arrival(res: Dict[str, Any]) -> Tuple[bool, str]:
    dep = res.get("departure_time")
    arr = res.get("arrival_time")
    if not dep or not arr:
        return True, ""
    try:
        if str(dep) >= str(arr):
            return False, f"departure_time ('{dep}') must precede arrival_time ('{arr}')"
    except Exception:
        pass
    return True, ""


def _validate_usd_currency_match(res: Dict[str, Any]) -> Tuple[bool, str]:
    price_usd = res.get("price_usd")
    currency = res.get("currency")
    if price_usd is not None and currency is not None:
        if str(currency).strip().upper() != "USD":
            return False, f"Field 'price_usd' requires currency='USD', got '{currency}'"
    return True, ""


CROSS_FIELD_RULES: List[CrossFieldRule] = [
    CrossFieldRule(
        rule_id="CFR-001",
        tool_names=["query_availability", "query_availability_google_calendar",
                    "query_availability_outlook_calendar", "query_availability_caldav"],
        fields_involved=["free_slots", "total_slots"],
        description="len(free_slots) <= total_slots",
        validator=_validate_free_slots_le_total,
        source="SOURCE_TOOL_CONTRACT",
        rationale="Number of free slots cannot exceed total slots in calendar availability query",
    ),
    CrossFieldRule(
        rule_id="CFR-002",
        tool_names=["*"],
        fields_involved=["start_time", "end_time"],
        description="start_time < end_time",
        validator=_validate_start_before_end,
        source="UNIVERSAL_DOMAIN_CONSTRAINT",
        rationale="Event start time must precede end time",
    ),
    CrossFieldRule(
        rule_id="CFR-003",
        tool_names=["get_hotel_info", "book_hotel", "search_hotels"],
        fields_involved=["check_in", "check_out"],
        description="check_in < check_out",
        validator=_validate_checkin_before_checkout,
        source="UNIVERSAL_DOMAIN_CONSTRAINT",
        rationale="Hotel check-in must precede check-out",
    ),
    CrossFieldRule(
        rule_id="CFR-004",
        tool_names=["get_flight_info", "book_flight", "search_flights"],
        fields_involved=["departure_time", "arrival_time"],
        description="departure_time < arrival_time",
        validator=_validate_departure_before_arrival,
        source="UNIVERSAL_DOMAIN_CONSTRAINT",
        rationale="Flight departure must precede arrival for same-day schedule",
    ),
    CrossFieldRule(
        rule_id="CFR-005",
        tool_names=["get_stock_yahoo_finance", "get_stock_alpha_vantage", "get_stock_finnhub"],
        fields_involved=["price_usd", "currency"],
        description="currency == 'USD' when price_usd is present",
        validator=_validate_usd_currency_match,
        source="SOURCE_TOOL_CONTRACT",
        rationale="price_usd field semantically mandates USD denomination",
    ),
]


def get_cross_field_rules_for_tool(tool_name: str, result: Dict[str, Any]) -> List[CrossFieldRule]:
    return [r for r in CROSS_FIELD_RULES if r.applies_to(tool_name, result)]
