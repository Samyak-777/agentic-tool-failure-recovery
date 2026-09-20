"""
tools/alternatives_loader.py - 替代关系加载器

加载和管理工具可替换关系，是 C2/C3/C4 复杂度设计的基础。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml


@dataclass
class AlternativePath:
    """单条替代路径"""
    path_id: str
    tools: List[Dict[str, Any]]


@dataclass
class AlternativeGroup:
    """一组可替换的路径"""
    alt_id: str
    description: str
    domain: str
    paths: List[AlternativePath]
    alt_type: str  # e.g. "one_to_one", "one_to_many", "many_to_many"
    output_schema: Optional[Dict[str, Any]] = None


def validate_many_to_many_group_config(
    alt_id: str,
    config: Dict[str, Any],
) -> List[str]:
    """校验 many_to_many group 是否满足当前仓库的结构约束。"""
    issues: List[str] = []
    paths = config.get("paths", [])

    if not isinstance(paths, list) or len(paths) < 2:
        return [f"{alt_id}: many_to_many must contain at least 2 paths"]

    path_tool_sets = []
    seen_path_ids = set()
    for idx, path in enumerate(paths, 1):
        if not isinstance(path, dict):
            issues.append(f"{alt_id}: path {idx} must be an object")
            continue

        path_id = str(path.get("path_id") or f"path_{idx}")
        if path_id in seen_path_ids:
            issues.append(f"{alt_id}: duplicate path_id '{path_id}'")
        seen_path_ids.add(path_id)

        tools = path.get("tools", [])
        if not isinstance(tools, list) or len(tools) < 2:
            issues.append(f"{alt_id}: path '{path_id}' must contain at least 2 tools")
            continue

        tool_names: List[str] = []
        for tool_idx, tool in enumerate(tools, 1):
            if not isinstance(tool, dict):
                issues.append(f"{alt_id}: path '{path_id}' tool {tool_idx} must be an object")
                continue
            tool_name = str(tool.get("tool_name") or "").strip()
            if not tool_name:
                issues.append(f"{alt_id}: path '{path_id}' tool {tool_idx} missing tool_name")
                continue
            tool_names.append(tool_name)

        local_dupes = sorted({name for name in tool_names if tool_names.count(name) > 1})
        if local_dupes:
            issues.append(
                f"{alt_id}: path '{path_id}' repeats tool(s) {local_dupes}"
            )

        path_tool_sets.append((path_id, set(tool_names)))

    for idx in range(len(path_tool_sets)):
        left_id, left_tools = path_tool_sets[idx]
        for jdx in range(idx + 1, len(path_tool_sets)):
            right_id, right_tools = path_tool_sets[jdx]
            overlap = sorted(left_tools & right_tools)
            if overlap:
                issues.append(
                    f"{alt_id}: paths '{left_id}' and '{right_id}' share tool(s) {overlap}"
                )

    return issues


def filter_valid_many_to_many_groups(
    groups: Dict[str, Any],
    verbose: bool = False,
) -> Dict[str, Any]:
    """过滤掉不满足 many_to_many 约束的 group。"""
    valid: Dict[str, Any] = {}
    for alt_id, config in (groups or {}).items():
        issues = validate_many_to_many_group_config(alt_id, config)
        if issues:
            if verbose:
                preview = "; ".join(issues)
                print(f"[alternatives] skip invalid many_to_many '{alt_id}': {preview}")
            continue
        valid[alt_id] = config
    return valid


class AlternativesLoader:
    """工具替代关系加载器"""

    def __init__(self, alternatives_file: str):
        self.alternatives_file = Path(alternatives_file)
        self.alternatives: Dict[str, AlternativeGroup] = {}
        self._load()

    def _load(self):
        """加载 alternatives.yaml"""
        if not self.alternatives_file.exists():
            return

        with open(self.alternatives_file) as f:
            data = yaml.safe_load(f)

        for alt_type, groups in data.get("alternatives", {}).items():
            if not isinstance(groups, dict):
                continue
            if alt_type == "many_to_many":
                groups = filter_valid_many_to_many_groups(groups)

            for alt_id, config in groups.items():
                paths = [
                    AlternativePath(
                        path_id=p["path_id"],
                        tools=p["tools"]
                    )
                    for p in config.get("paths", [])
                ]
                self.alternatives[alt_id] = AlternativeGroup(
                    alt_id=alt_id,
                    description=config.get("description", ""),
                    domain=config.get("domain", ""),
                    paths=paths,
                    alt_type=alt_type,
                    output_schema=config.get("output_schema")
                )

    def get_alternative_group(self, alt_id: str) -> Optional[AlternativeGroup]:
        """获取指定的替代组"""
        return self.alternatives.get(alt_id)

    def get_all_alternatives_by_type(self, alt_type: str) -> List[AlternativeGroup]:
        """获取指定类型的所有替代组"""
        return [
            alt for alt in self.alternatives.values()
            if alt.alt_type == alt_type
        ]

    def list_all_groups(self) -> List[str]:
        """列出所有替代组ID"""
        return list(self.alternatives.keys())
