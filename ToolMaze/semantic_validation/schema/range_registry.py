"""
semantic_validation/schema/range_registry.py

Explicit value range rules for ToolMaze tool outputs.

IMPORTANT RESEARCH CONSTRAINT:
    Every rule in this registry MUST declare:
        - source:    One of the four allowed categories below.
        - rationale: Why this constraint exists.
        - scope:     "universal" | "domain" | "tool_specific"

    Allowed source categories:
        SOURCE_TOOL_CONTRACT      — constraint declared in ToolMaze tool YAML/plugin
        UNIVERSAL_DOMAIN_CONSTRAINT — universally true for the domain (verifiable
                                      from external authoritative sources)
        EXPLICIT_PROJECT_RULE     — introduced by this research; must be documented
                                    in assumptions.md and justified explicitly
        HEURISTIC                 — not formally derivable; may introduce false
                                    positives; flagged with elevated risk

    Rules with source=HEURISTIC must be reviewed before paper submission
    and may be excluded from claims about "deterministic" validation.

    NEVER add a rule because it "seems reasonable." Either cite a source or
    do not add it. The empty registry is a valid starting state.

    For the initial deterministic experiment (Phases B–D) only
    SOURCE_TOOL_CONTRACT and UNIVERSAL_DOMAIN_CONSTRAINT rules are used.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Rule source categories
# ---------------------------------------------------------------------------

class RuleSource:
    SOURCE_TOOL_CONTRACT = "SOURCE_TOOL_CONTRACT"
    UNIVERSAL_DOMAIN_CONSTRAINT = "UNIVERSAL_DOMAIN_CONSTRAINT"
    EXPLICIT_PROJECT_RULE = "EXPLICIT_PROJECT_RULE"
    HEURISTIC = "HEURISTIC"


# ---------------------------------------------------------------------------
# Range rule dataclass
# ---------------------------------------------------------------------------

@dataclass
class RangeRule:
    """
    A single value range constraint for a specific output field.

    Attributes:
        rule_id:        Unique identifier (e.g., "RR-001").
        tool_names:     List of tool names this rule applies to.
                        Use ["*"] for universal rules that apply to any tool
                        with this field name.
        field_name:     Output field the range applies to.
        min_val:        Minimum allowed value (None = no lower bound).
        max_val:        Maximum allowed value (None = no upper bound).
        inclusive_min:  True if min_val is included in valid range (≥ vs >).
        inclusive_max:  True if max_val is included in valid range (≤ vs <).
        source:         One of RuleSource constants.
        scope:          "universal" | "domain" | "tool_specific".
        rationale:      Explanation of why this constraint exists.
        risk:           "low" | "medium" | "high" — FP risk if rule is wrong.
        references:     Optional external citations or links.
    """
    rule_id: str
    tool_names: List[str]
    field_name: str
    min_val: Optional[float]
    max_val: Optional[float]
    inclusive_min: bool = True
    inclusive_max: bool = True
    source: str = RuleSource.EXPLICIT_PROJECT_RULE
    scope: str = "tool_specific"
    rationale: str = ""
    risk: str = "medium"
    references: List[str] = field(default_factory=list)

    def applies_to(self, tool_name: str) -> bool:
        """True if this rule applies to the given tool."""
        return "*" in self.tool_names or tool_name in self.tool_names

    def check(self, value: Any) -> Tuple[bool, str]:
        """
        Check whether a numeric value satisfies this range constraint.

        Args:
            value: The field value from the tool output. Must be numeric.

        Returns:
            (passed: bool, failure_message: str)
            failure_message is empty string if passed.
        """
        if not isinstance(value, (int, float)):
            return False, (
                f"Field '{self.field_name}' expected numeric value for range "
                f"check, got {type(value).__name__}: {value!r}"
            )

        violations = []

        if self.min_val is not None:
            if self.inclusive_min:
                if value < self.min_val:
                    violations.append(
                        f"{value} < min({self.min_val}) [{self.rule_id}]"
                    )
            else:
                if value <= self.min_val:
                    violations.append(
                        f"{value} <= min({self.min_val}) (exclusive) [{self.rule_id}]"
                    )

        if self.max_val is not None:
            if self.inclusive_max:
                if value > self.max_val:
                    violations.append(
                        f"{value} > max({self.max_val}) [{self.rule_id}]"
                    )
            else:
                if value >= self.max_val:
                    violations.append(
                        f"{value} >= max({self.max_val}) (exclusive) [{self.rule_id}]"
                    )

        if violations:
            return False, (
                f"Range violation for '{self.field_name}': "
                + "; ".join(violations)
                + f" | Rationale: {self.rationale}"
            )
        return True, ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "tool_names": self.tool_names,
            "field_name": self.field_name,
            "min_val": self.min_val,
            "max_val": self.max_val,
            "inclusive_min": self.inclusive_min,
            "inclusive_max": self.inclusive_max,
            "source": self.source,
            "scope": self.scope,
            "rationale": self.rationale,
            "risk": self.risk,
            "references": self.references,
        }


# ---------------------------------------------------------------------------
# Range registry
# ---------------------------------------------------------------------------

class RangeRegistry:
    """
    Collection of all explicit range rules.

    Methods:
        get_rules(tool_name, field_name): Return applicable rules.
        all_rules():                      Return all rules (for coverage report).
    """

    def __init__(self) -> None:
        self._rules: List[RangeRule] = []
        self._build_rules()

    def _build_rules(self) -> None:
        """
        Define all range rules.

        ADDING A RULE:
            1. Assign a unique rule_id (RR-XXX, sequential).
            2. Cite source and rationale explicitly.
            3. Set appropriate risk level.
            4. Add to assumptions.md.
            5. If source=HEURISTIC, raise review flag in assumptions.md.

        Current rules (initial set for Phases B–D):
        """

        # ------------------------------------------------------------------
        # RR-001: Stock price must be positive
        # Source: UNIVERSAL_DOMAIN_CONSTRAINT
        # Rationale: Stock prices are defined as positive real numbers in
        #            financial markets. A zero or negative price indicates
        #            data corruption or API error.
        # Scope: domain (Financial)
        # Risk: low — universally true for publicly traded stocks
        # References: CFA Institute "Equity Valuation" — price > 0 by definition
        # ------------------------------------------------------------------
        self._rules.append(RangeRule(
            rule_id="RR-001",
            tool_names=[
                "get_stock_yahoo_finance",
                "get_stock_alpha_vantage",
                "get_stock_finnhub",
            ],
            field_name="price_usd",
            min_val=0.0,
            max_val=None,
            inclusive_min=False,   # strictly > 0
            source=RuleSource.UNIVERSAL_DOMAIN_CONSTRAINT,
            scope="domain",
            rationale=(
                "Stock prices are positive real numbers by financial market "
                "definition. A value ≤ 0 indicates data corruption or an "
                "invalid API response."
            ),
            risk="low",
            references=["CFA Institute Equity Valuation textbook", "SEC market rules"],
        ))

        # ------------------------------------------------------------------
        # RR-002: Cryptocurrency price must be positive
        # Source: UNIVERSAL_DOMAIN_CONSTRAINT (same logic as RR-001)
        # ------------------------------------------------------------------
        self._rules.append(RangeRule(
            rule_id="RR-002",
            tool_names=[
                "get_crypto_price_coingecko",
                "get_crypto_price_coinmarketcap",
            ],
            field_name="price_usd",
            min_val=0.0,
            max_val=None,
            inclusive_min=False,
            source=RuleSource.UNIVERSAL_DOMAIN_CONSTRAINT,
            scope="domain",
            rationale=(
                "Cryptocurrency prices are positive. A value ≤ 0 is physically "
                "and economically impossible for a listed asset."
            ),
            risk="low",
            references=["CoinMarketCap API docs", "CoinGecko API docs"],
        ))

        # ------------------------------------------------------------------
        # RR-003: Exchange rate must be positive
        # Source: UNIVERSAL_DOMAIN_CONSTRAINT
        # Rationale: A currency exchange rate is a ratio of two positive
        #            quantities; it is therefore always > 0.
        # ------------------------------------------------------------------
        self._rules.append(RangeRule(
            rule_id="RR-003",
            tool_names=[
                "get_exchange_rate_currencyapi",
                "get_exchange_rate_exchangerate",
                "get_exchange_rate_fixer",
            ],
            field_name="rate",
            min_val=0.0,
            max_val=None,
            inclusive_min=False,
            source=RuleSource.UNIVERSAL_DOMAIN_CONSTRAINT,
            scope="domain",
            rationale=(
                "An exchange rate is the ratio of two positive currency values, "
                "therefore always > 0. Rate ≤ 0 is physically impossible."
            ),
            risk="low",
            references=["BIS FX market conventions", "ISO 4217"],
        ))

        # ------------------------------------------------------------------
        # RR-004: total_slots in availability query must be non-negative
        # Source: SOURCE_TOOL_CONTRACT
        # Rationale: Derived from query_availability plugin: total_slots is a
        #            count of available slots (integer ≥ 0).
        # ------------------------------------------------------------------
        self._rules.append(RangeRule(
            rule_id="RR-004",
            tool_names=["query_availability",
                        "query_availability_google_calendar",
                        "query_availability_outlook_calendar",
                        "query_availability_caldav"],
            field_name="total_slots",
            min_val=0,
            max_val=None,
            inclusive_min=True,
            source=RuleSource.SOURCE_TOOL_CONTRACT,
            scope="tool_specific",
            rationale=(
                "total_slots is a count of calendar slots. It cannot be negative. "
                "Source: query_availability plugin CASES dict and output schema."
            ),
            risk="low",
            references=["tools/plugins/query_availability.py"],
        ))

        # ------------------------------------------------------------------
        # NOTE: Temperature range is intentionally NOT added.
        # Rationale: ToolMaze's weather tools return deterministic temperatures
        # (e.g. Tokyo=22°C, Paris=18°C). The tool contract does not specify a
        # valid temperature range. While physical atmospheric temperatures are
        # bounded, asserting those bounds would be an EXPLICIT_PROJECT_RULE
        # assumption not grounded in the tool contract, and could create false
        # positives if the perturbation injects an extreme-but-plausible value.
        # Decision: omit. Document in assumptions.md.
        #
        # NOTE: Percentage fields (0–100) are NOT added universally.
        # ToolMaze does not have tools returning percentages at this time.
        # ------------------------------------------------------------------

    def get_rules(
        self, tool_name: str, field_name: str
    ) -> List[RangeRule]:
        """
        Return all range rules applicable to a specific tool + field.

        Args:
            tool_name:  Tool being validated.
            field_name: Output field being checked.

        Returns:
            List of matching RangeRule objects (may be empty).
        """
        return [
            r for r in self._rules
            if r.applies_to(tool_name) and r.field_name == field_name
        ]

    def get_tools_with_rules(self, tool_name: str) -> List[str]:
        """Return all field names that have rules for this tool."""
        return list({
            r.field_name for r in self._rules if r.applies_to(tool_name)
        })

    def all_rules(self) -> List[RangeRule]:
        """Return all registered rules (for coverage reporting)."""
        return list(self._rules)

    def rules_for_coverage_report(self) -> List[Dict[str, Any]]:
        """Serialize all rules for the tool coverage JSON report."""
        return [r.to_dict() for r in self._rules]
