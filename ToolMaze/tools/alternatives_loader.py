
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
    alt_type: str
    output_schema: Optional[Dict[str, Any]] = None


def validate_group_config(
    alt_id: str,
    config: Any,
    alt_type: str,
) -> List[str]:
    """Validate the basic structure of an alternative group."""

    issues: List[str] = []

    if not isinstance(config, dict):
        return [f"{alt_id}: group config must be an object"]

    paths = config.get("paths")

    if not isinstance(paths, list) or not paths:
        return [f"{alt_id}: paths must be a non-empty list"]

    if alt_type == "many_to_many" and len(paths) < 2:
        issues.append(
            f"{alt_id}: many_to_many must contain at least 2 paths"
        )

    path_tool_sets = []
    seen_path_ids = set()

    for idx, path in enumerate(paths, 1):
        if not isinstance(path, dict):
            issues.append(
                f"{alt_id}: path {idx} must be an object"
            )
            continue

        path_id = str(path.get("path_id") or "").strip()

        if not path_id:
            issues.append(
                f"{alt_id}: path {idx} missing path_id"
            )
            continue

        if path_id in seen_path_ids:
            issues.append(
                f"{alt_id}: duplicate path_id '{path_id}'"
            )

        seen_path_ids.add(path_id)

        tools = path.get("tools")

        if not isinstance(tools, list) or not tools:
            issues.append(
                f"{alt_id}: path '{path_id}' must contain a non-empty tools list"
            )
            continue

        if alt_type == "many_to_many" and len(tools) < 2:
            issues.append(
                f"{alt_id}: path '{path_id}' must contain at least 2 tools"
            )

        tool_names = []

        for tool_idx, tool in enumerate(tools, 1):
            if not isinstance(tool, dict):
                issues.append(
                    f"{alt_id}: path '{path_id}' tool {tool_idx} must be an object"
                )
                continue

            tool_name = str(tool.get("tool_name") or "").strip()

            if not tool_name:
                issues.append(
                    f"{alt_id}: path '{path_id}' tool {tool_idx} missing tool_name"
                )
                continue

            tool_names.append(tool_name)

        local_dupes = sorted(
            {
                name for name in tool_names
                if tool_names.count(name) > 1
            }
        )

        if local_dupes:
            issues.append(
                f"{alt_id}: path '{path_id}' repeats tool(s) {local_dupes}"
            )

        path_tool_sets.append((path_id, set(tool_names)))

    # many_to_many paths must not share tools.
    if alt_type == "many_to_many":
        for idx in range(len(path_tool_sets)):
            left_id, left_tools = path_tool_sets[idx]

            for jdx in range(idx + 1, len(path_tool_sets)):
                right_id, right_tools = path_tool_sets[jdx]

                overlap = sorted(left_tools & right_tools)

                if overlap:
                    issues.append(
                        f"{alt_id}: paths '{left_id}' and "
                        f"'{right_id}' share tool(s) {overlap}"
                    )

    return issues


def validate_many_to_many_group_config(
    alt_id: str,
    config: Dict[str, Any],
) -> List[str]:
    """校验 many_to_many group 是否满足当前仓库的结构约束。"""

    return validate_group_config(
        alt_id=alt_id,
        config=config,
        alt_type="many_to_many",
    )


def filter_valid_many_to_many_groups(
    groups: Dict[str, Any],
    verbose: bool = False,
) -> Dict[str, Any]:
    """过滤掉不满足 many_to_many 约束的 group。"""

    valid: Dict[str, Any] = {}

    if not isinstance(groups, dict):
        return valid

    for alt_id, config in groups.items():
        issues = validate_many_to_many_group_config(
            alt_id,
            config,
        )

        if issues:
            if verbose:
                preview = "; ".join(issues)
                print(
                    f"[alternatives] skip invalid many_to_many "
                    f"'{alt_id}': {preview}"
                )
            continue

        valid[alt_id] = config

    return valid


class AlternativesLoader:
    """工具替代关系加载器"""

    def __init__(
        self,
        alternatives_file: str,
        verbose: bool = False,
    ):
        self.alternatives_file = Path(alternatives_file)
        self.alternatives: Dict[str, AlternativeGroup] = {}
        self.validation_issues: List[str] = []
        self.verbose = verbose

        self._load()

    def _load(self):
        """加载 alternatives.yaml"""

        if not self.alternatives_file.exists():
            if self.verbose:
                print(
                    f"[alternatives] file not found: "
                    f"{self.alternatives_file}"
                )
            return

        try:
            with open(
                self.alternatives_file,
                "r",
                encoding="utf-8",
            ) as f:
                data = yaml.safe_load(f)

        except (OSError, yaml.YAMLError) as exc:
            self.validation_issues.append(
                f"Failed to load alternatives file: {exc}"
            )

            if self.verbose:
                print(
                    f"[alternatives] load error: {exc}"
                )

            return

        if data is None:
            return

        if not isinstance(data, dict):
            self.validation_issues.append(
                "YAML root must be an object"
            )
            return

        alternatives = data.get("alternatives", {})

        if not isinstance(alternatives, dict):
            self.validation_issues.append(
                "'alternatives' must be an object"
            )
            return

        for alt_type, groups in alternatives.items():

            if not isinstance(groups, dict):
                self.validation_issues.append(
                    f"'{alt_type}' must contain an object of groups"
                )
                continue

            for alt_id, config in groups.items():

                issues = validate_group_config(
                    alt_id,
                    config,
                    alt_type,
                )

                if issues:
                    self.validation_issues.extend(issues)

                    if self.verbose:
                        for issue in issues:
                            print(
                                f"[alternatives] skip invalid group: {issue}"
                            )

                    continue

                if alt_id in self.alternatives:
                    issue = (
                        f"Duplicate alternative group ID '{alt_id}'"
                    )
                    self.validation_issues.append(issue)

                    if self.verbose:
                        print(f"[alternatives] {issue}")

                    continue

                paths = [
                    AlternativePath(
                        path_id=path["path_id"],
                        tools=path["tools"],
                    )
                    for path in config["paths"]
                ]

                self.alternatives[alt_id] = AlternativeGroup(
                    alt_id=alt_id,
                    description=config.get("description", ""),
                    domain=config.get("domain", ""),
                    paths=paths,
                    alt_type=alt_type,
                    output_schema=config.get("output_schema"),
                )

    def get_alternative_group(
        self,
        alt_id: str,
    ) -> Optional[AlternativeGroup]:
        """获取指定的替代组"""

        return self.alternatives.get(alt_id)

    def get_all_alternatives_by_type(
        self,
        alt_type: str,
    ) -> List[AlternativeGroup]:
        """获取指定类型的所有替代组"""

        return [
            alt
            for alt in self.alternatives.values()
            if alt.alt_type == alt_type
        ]

    def list_all_groups(self) -> List[str]:
        """列出所有替代组ID"""

        return list(self.alternatives.keys())
