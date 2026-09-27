"""
semantic_validation/core/state_store.py

Isolated validation state store for cross-call consistency tracking (L8).

Design principles:
    1. Completely isolated per execution_id (UUID per benchmark run).
       State is NEVER shared between ToolMaze tasks.
    2. task_id is stored separately for reporting — it does NOT serve as
       the isolation key.
    3. The state store does NOT have access to perturbation labels,
       ground truth, or oracle paths.
    4. State rules are explicit and documented. No implicit accumulation.

Research note:
    ExecutionValidationStateStore is keyed by execution_id (UUID).
    In the parallel ThreadPoolExecutor, each task gets a fresh UUID
    at ExecutionEngine init time, so isolation is guaranteed even
    under concurrent execution.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Observation record
# ---------------------------------------------------------------------------

@dataclass
class FieldObservation:
    """
    A single observed field value recorded during validation.

    Attributes:
        tool_name:   Tool that produced this observation.
        field_name:  Name of the observed output field.
        value:       Observed value (must be serialisable).
        step:        Tool call step number.
        arguments:   Arguments the tool was called with (for context).
    """
    tool_name: str
    field_name: str
    value: Any
    step: int
    arguments: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Per-execution state
# ---------------------------------------------------------------------------

@dataclass
class ExecutionValidationState:
    """
    Mutable validation state for one benchmark task execution.

    Stores:
        execution_id:       UUID assigned at task start. Isolation key.
        task_id:            ToolMaze task_id for reporting only.
        observations:       History of all observed field values.
        entity_registry:    Established entity bindings
                            {entity_type: (value, step, tool_name)}.
                            E.g. {"user_alice_id": ("u_alice", 2, "get_contact_info")}
        flagged_steps:      Steps where state inconsistency was detected.

    Thread-safety note:
        This object is owned by a single ExecutionEngine instance which
        is itself created fresh per task. No concurrent access within one
        state object. The state_store (outer dict) is protected by a lock.
    """
    execution_id: str
    task_id: str
    observations: List[FieldObservation] = field(default_factory=list)
    entity_registry: Dict[str, Tuple[Any, int, str]] = field(default_factory=dict)
    flagged_steps: List[int] = field(default_factory=list)

    # -----------------------------------------------------------------------
    # Observation recording
    # -----------------------------------------------------------------------

    def record_observation(
        self,
        tool_name: str,
        field_name: str,
        value: Any,
        step: int,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store an observed field value from a validated tool output.

        Only called by StateChecker (L8) for fields covered by explicit
        state rules. Not called for every field of every output.

        Args:
            tool_name:  Tool name.
            field_name: Output field name.
            value:      Observed value.
            step:       Step number.
            arguments:  Tool call arguments (for entity context).
        """
        self.observations.append(
            FieldObservation(
                tool_name=tool_name,
                field_name=field_name,
                value=value,
                step=step,
                arguments=arguments or {},
            )
        )

    def get_prior_observations(
        self,
        field_name: str,
        tool_name: Optional[str] = None,
    ) -> List[FieldObservation]:
        """
        Retrieve all prior observations of a field, optionally filtered by tool.

        Args:
            field_name: Field to look up.
            tool_name:  If specified, only return observations from that tool.

        Returns:
            List of FieldObservation, oldest first.
        """
        return [
            obs for obs in self.observations
            if obs.field_name == field_name
            and (tool_name is None or obs.tool_name == tool_name)
        ]

    # -----------------------------------------------------------------------
    # Entity registry
    # -----------------------------------------------------------------------

    def register_entity(
        self,
        entity_key: str,
        value: Any,
        step: int,
        tool_name: str,
    ) -> None:
        """
        Establish an entity binding.

        Called by StateChecker when a canonical entity identifier is first
        observed (e.g., user_id for a specific person).

        Entity key convention: "{entity_type}:{canonical_name}"
        Example: "user_id:alice"

        Args:
            entity_key: Composite key identifying the entity.
            value:      The observed identifier value.
            step:       Step at which it was established.
            tool_name:  Tool that produced it.
        """
        if entity_key not in self.entity_registry:
            self.entity_registry[entity_key] = (value, step, tool_name)

    def get_entity(
        self, entity_key: str
    ) -> Optional[Tuple[Any, int, str]]:
        """
        Look up a registered entity binding.

        Args:
            entity_key: Composite entity key.

        Returns:
            Tuple (value, step, tool_name) or None if not registered.
        """
        return self.entity_registry.get(entity_key)

    def flag_step(self, step: int) -> None:
        """Mark a step as having a state inconsistency."""
        if step not in self.flagged_steps:
            self.flagged_steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for trace logging."""
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "observation_count": len(self.observations),
            "entity_count": len(self.entity_registry),
            "flagged_steps": self.flagged_steps,
        }


# ---------------------------------------------------------------------------
# State store — global registry of per-execution states
# ---------------------------------------------------------------------------

class ValidationStateStore:
    """
    Thread-safe registry mapping execution_id → ExecutionValidationState.

    Lifecycle:
        create_state(execution_id, task_id) → called at task start.
        get_state(execution_id)             → called by checkers during validation.
        destroy_state(execution_id)         → called at task end (cleanup).

    No state leaks between tasks because each gets a unique execution_id (UUID).
    """

    def __init__(self) -> None:
        self._states: Dict[str, ExecutionValidationState] = {}
        self._lock = threading.Lock()

    def create_state(self, execution_id: str, task_id: str) -> ExecutionValidationState:
        """
        Create and register a fresh state for a new execution.

        Args:
            execution_id: UUID for this execution. Must be unique.
            task_id:      ToolMaze task_id for reporting.

        Returns:
            The newly created ExecutionValidationState.

        Raises:
            ValueError: If execution_id already exists (indicates a UUID
                        collision or incorrect lifecycle management).
        """
        with self._lock:
            if execution_id in self._states:
                raise ValueError(
                    f"State already exists for execution_id={execution_id}. "
                    "Possible UUID collision or create_state called twice."
                )
            state = ExecutionValidationState(
                execution_id=execution_id,
                task_id=task_id,
            )
            self._states[execution_id] = state
            return state

    def get_state(self, execution_id: str) -> Optional[ExecutionValidationState]:
        """
        Retrieve the state for an active execution.

        Args:
            execution_id: UUID of the execution.

        Returns:
            ExecutionValidationState or None if not found.
        """
        with self._lock:
            return self._states.get(execution_id)

    def destroy_state(self, execution_id: str) -> None:
        """
        Remove and discard the state for a completed execution.

        Idempotent — safe to call even if state was already removed.

        Args:
            execution_id: UUID of the execution to clean up.
        """
        with self._lock:
            self._states.pop(execution_id, None)

    def active_count(self) -> int:
        """Number of currently active execution states (for diagnostics)."""
        with self._lock:
            return len(self._states)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

# Single global store shared by all ExecutionEngine instances.
# Thread-safe by design. Each task gets an isolated ExecutionValidationState.
GLOBAL_STATE_STORE = ValidationStateStore()
