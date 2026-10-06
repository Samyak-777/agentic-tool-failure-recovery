"""
semantic_validation/schema/extractor.py

Extracts output schemas from ToolMaze tool definitions.

SOURCE of schema data:
    Each tool in tools/definitions/*.yaml has a 'mcp' section that contains
    an 'output_schema' dict mapping field names to {type, ...} dicts.

    This schema was written by the ToolMaze benchmark authors as the
    tool output contract. It is used verbatim — no schema is invented.

    The 'function_call' section has the INPUT parameter schema.
    The 'mcp.output_schema' has the OUTPUT schema.

Research note:
    ASSUMPTION: "The output_schema in the MCP section of each tool definition
    represents the authoritative output contract for that tool."
    Source: ToolMaze YAML files (SOURCE_TOOL_CONTRACT).
    Risk: Low — written by benchmark authors. Verified manually for sample tools.

    If output_schema is absent, SchemaExtractor returns None and the
    dependent checkers (schema, type, required) return NOT_APPLICABLE.
    We do NOT invent schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class SchemaExtractor:
    """
    Extracts output schemas from ToolLoader-loaded tool definitions.

    Caches results after first extraction to avoid repeated YAML traversal.

    Usage:
        extractor = SchemaExtractor(tool_loader)
        schema = extractor.get_output_schema("get_weather_openweather")
        # Returns: {"temperature_celsius": {"type": "integer"}, "condition": {"type": "string"}}
        # or None if not available.
    """

    def __init__(self, tool_loader: Any) -> None:
        """
        Args:
            tool_loader: An instance of tools.loader.ToolLoader.
        """
        self._loader = tool_loader
        self._cache: Dict[str, Optional[Dict[str, Any]]] = {}

    def get_output_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Return the MCP output schema for a tool, or None if unavailable.

        Args:
            tool_name: Tool name (e.g., "get_weather_openweather").

        Returns:
            Dict of {field_name: {type: str, ...}} or None.
        """
        if tool_name in self._cache:
            return self._cache[tool_name]

        schema = self._extract(tool_name)
        self._cache[tool_name] = schema
        return schema

    def _extract(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Internal extraction from ToolLoader."""
        tool_def = self._loader.get_tool_by_name(tool_name)
        if not tool_def:
            return None

        # Navigate: paradigms → mcp → output_schema
        mcp = tool_def.get("paradigms", {}).get("mcp", {})
        if not mcp:
            return None

        output_schema = mcp.get("output_schema")
        if not output_schema or not isinstance(output_schema, dict):
            return None

        return output_schema

    def get_input_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Return the function_call input parameter schema for a tool.

        Used by cross-field and entity checkers to understand what the
        agent requested, without looking at oracle data.

        Args:
            tool_name: Tool name.

        Returns:
            Dict with 'properties' and 'required' keys, or None.
        """
        tool_def = self._loader.get_tool_by_name(tool_name)
        if not tool_def:
            return None
        return (
            tool_def.get("paradigms", {})
            .get("function_call", {})
            .get("spec", {})
            .get("parameters")
        )

    def get_expected_output_fields(self, tool_name: str) -> List[str]:
        """
        Return list of expected output field names from the MCP schema.

        Args:
            tool_name: Tool name.

        Returns:
            List of field names (may be empty if schema unavailable).
        """
        schema = self.get_output_schema(tool_name)
        if schema is None:
            return []
        return list(schema.keys())

    def schema_available(self, tool_name: str) -> bool:
        """True if an output schema exists for this tool."""
        return self.get_output_schema(tool_name) is not None

    def get_field_type(self, tool_name: str, field_name: str) -> Optional[str]:
        """
        Return the declared type of a specific output field.

        Args:
            tool_name:  Tool name.
            field_name: Field name.

        Returns:
            Type string (e.g., "integer", "string") or None.
        """
        schema = self.get_output_schema(tool_name)
        if schema is None:
            return None
        field_def = schema.get(field_name, {})
        return field_def.get("type") if isinstance(field_def, dict) else None
