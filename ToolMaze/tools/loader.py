"""
Unified Tool Loader
Automatically loads all YAML files from definitions/ and indexes them by category

Usage:
    from tools.loader import ToolLoader

    loader = ToolLoader("tools/definitions")

    # Get all Source category tools
    source_tools = loader.get_tools_by_category("Source")

    # Randomly sample 2 Processor tools
    processors = loader.sample_by_category("Processor", n=2)

    # Get tool by name
    tool = loader.get_tool_by_name("get_weather_openweather")
"""

import yaml
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ToolLoader:
    """Unified tool loader that supports organizing and querying by category"""

    def __init__(self, definitions_dir: str = "definitions"):
        """
        Initialize tool loader

        Args:
            definitions_dir: Directory containing tool definition files (YAML files)
        """
        self.definitions_dir = Path(definitions_dir)
        self.tools_by_category: Dict[str, List[Dict]] = {}  # {"Source": [...], "Processor": [...]}
        self.tools_by_name: Dict[str, Dict] = {}            # {"get_weather_openweather": {...}}
        self._load_all()

    def _load_all(self):
        """Automatically load all YAML files"""
        if not self.definitions_dir.exists():
            raise FileNotFoundError(f"Definitions directory not found: {self.definitions_dir}")

        yaml_files = list(self.definitions_dir.glob("*.yaml"))
        if not yaml_files:
            raise FileNotFoundError(f"No YAML files found in {self.definitions_dir}")

        for yaml_file in yaml_files:
            self._load_file(yaml_file)

    def _load_file(self, yaml_file: Path):
        """Load a single YAML file"""
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        tools = data.get('tools', [])
        if not tools:
            return

        # Get category from tool data, not inferred from filename
        for tool in tools:
            category = tool.get('category', 'Unknown')

            # Index by category
            if category not in self.tools_by_category:
                self.tools_by_category[category] = []
            self.tools_by_category[category].append(tool)

            # Index by name
            tool_name = tool.get('name')
            if tool_name:
                self.tools_by_name[tool_name] = tool

    def get_tools_by_category(self, category: str) -> List[Dict]:
        """
        Get tool list by category

        Args:
            category: Tool category (Source, Processor, Action)

        Returns:
            List of all tool definitions in that category
        """
        return self.tools_by_category.get(category, [])

    def get_all_categories(self) -> List[str]:
        """Get all available tool categories"""
        return list(self.tools_by_category.keys())

    def sample_by_category(self, category: str, n: int = 1, seed: Optional[int] = None) -> List[Dict]:
        """
        Randomly sample n tools from a category

        Args:
            category: Tool category
            n: Sample size
            seed: Random seed (for reproducible sampling)

        Returns:
            List of sampled tool definitions
        """
        tools = self.get_tools_by_category(category)
        if not tools:
            return []

        if seed is not None:
            random.seed(seed)

        return random.sample(tools, min(n, len(tools)))

    def get_tool_by_name(self, name: str) -> Optional[Dict]:
        """
        Get tool definition by name

        Args:
            name: Tool name

        Returns:
            Tool definition dictionary, or None if not found
        """
        return self.tools_by_name.get(name)

    def get_all_tool_names(self) -> List[str]:
        """Get all tool names"""
        return list(self.tools_by_name.keys())

    def get_tool_count(self) -> int:
        """Get total number of tools"""
        return len(self.tools_by_name)

    def get_category_stats(self) -> Dict[str, int]:
        """
        Get statistics for each category

        Returns:
            {"Source": 4, "Processor": 5, ...}
        """
        return {
            category: len(tools)
            for category, tools in self.tools_by_category.items()
        }

    def validate_tool_exists(self, tool_name: str) -> bool:
        """Check if a tool exists"""
        return tool_name in self.tools_by_name

    def get_substitutes(self, tool_name: str) -> List[str]:
        """
        Get list of substitute tools for a given tool

        Args:
            tool_name: Tool name

        Returns:
            List of substitute tool names
        """
        tool = self.get_tool_by_name(tool_name)
        if tool:
            return tool.get('substitutes', [])
        return []

    def find_similar_tools_vector(
        self,
        anchor_tool_name: str,
        min_similarity: float = 0.85,
        max_similarity: float = 0.99,
        top_k: Optional[int] = None,
        vector_index_dir: str = "data/vectors"
    ) -> List[Dict]:
        """
        Find similar tools using vector similarity search.

        This method integrates the VectorToolRetriever for fast similarity search.
        Useful for C2 factory's heterogeneous pair finding.

        Args:
            anchor_tool_name: Name of the anchor tool
            min_similarity: Minimum cosine similarity (default: 0.85)
            max_similarity: Maximum cosine similarity (default: 0.99)
            top_k: Maximum number of results (None = all)
            vector_index_dir: Path to vector index directory

        Returns:
            List of similar tool metadata with similarity scores

        Example:
            >>> loader = ToolLoader("tools/definitions")
            >>> similar = loader.find_similar_tools_vector("get_weather_openweather")
            >>> # Returns tools like "get_weather_weatherapi"
        """
        try:
            from .vector_retriever import VectorToolRetriever
        except ImportError:
            raise ImportError(
                "VectorToolRetriever not available. "
                "Make sure vector_retriever.py is in the tools directory."
            )

        retriever = VectorToolRetriever(index_dir=vector_index_dir)
        return retriever.find_similar_tools(
            anchor_tool_name=anchor_tool_name,
            min_similarity=min_similarity,
            max_similarity=max_similarity,
            top_k=top_k
        )

    def find_heterogeneous_pairs(
        self,
        category: Optional[str] = None,
        domain: Optional[str] = None,
        min_similarity: float = 0.85,
        max_similarity: float = 0.99,
        min_pairs: int = 1,
        vector_index_dir: str = "data/vectors"
    ) -> List[Tuple[str, List[Dict]]]:
        """
        Find heterogeneous tool pairs for C2 construction.

        This method finds tools that are semantically similar (similar functionality)
        but structurally different (different parameter names/formats).

        Args:
            category: Filter by category (e.g., "Source", "Processor")
            domain: Filter by domain (e.g., "Financial", "Travel")
            min_similarity: Minimum similarity threshold
            max_similarity: Maximum similarity threshold
            min_pairs: Minimum number of pairs to find
            vector_index_dir: Path to vector index directory

        Returns:
            List of (anchor_tool, similar_tools) tuples

        Example:
            >>> loader = ToolLoader("tools/definitions")
            >>> pairs = loader.find_heterogeneous_pairs(category="Source", domain="Travel")
            >>> # Returns pairs like ("get_weather_openweather", ["get_weather_weatherapi"])
        """
        try:
            from .vector_retriever import VectorToolRetriever
        except ImportError:
            raise ImportError(
                "VectorToolRetriever not available. "
                "Make sure vector_retriever.py is in the tools directory."
            )

        retriever = VectorToolRetriever(index_dir=vector_index_dir)
        pairs = []

        # Get candidate anchor tools
        tools = self.tools_by_name.values()

        if category:
            tools = [t for t in tools if t.get('category') == category]

        if domain:
            tools = [t for t in tools if t.get('domain') == domain]

        # Try to find pairs for each candidate
        for tool in tools:
            tool_name = tool['name']
            similar = retriever.find_similar_tools(
                anchor_tool_name=tool_name,
                min_similarity=min_similarity,
                max_similarity=max_similarity
            )

            if similar:
                pairs.append((tool_name, similar))

            if len(pairs) >= min_pairs:
                break

        return pairs


def load_tool_definitions(definitions_dir: str = "definitions") -> ToolLoader:
    """
    Convenience function: load tool definitions

    Args:
        definitions_dir: Directory containing definition files

    Returns:
        ToolLoader instance
    """
    return ToolLoader(definitions_dir)


if __name__ == '__main__':
    # Test loader
    import os

    # Get correct path
    current_dir = Path(__file__).parent
    definitions_dir = current_dir / "definitions"

    print("=== Tool Loader Test ===\n")

    try:
        loader = ToolLoader(str(definitions_dir))

        print(f"✓ Successfully loaded tool definition directory: {definitions_dir}")
        print(f"✓ Total tools: {loader.get_tool_count()}\n")

        # Show category statistics
        print("=== Category Statistics ===")
        stats = loader.get_category_stats()
        for category, count in stats.items():
            print(f"  {category}: {count} tools")
        print()

        # Test getting by category
        print("=== Source Category Tools ===")
        source_tools = loader.get_tools_by_category("Source")
        for tool in source_tools:
            print(f"  - {tool['name']}: {tool['description']}")
        print()

        # Test sampling
        print("=== Random Sampling (Processor, n=2) ===")
        sampled = loader.sample_by_category("Processor", n=2, seed=42)
        for tool in sampled:
            print(f"  - {tool['name']}")
        print()

        # Test getting by name
        print("=== Get Tool by Name ===")
        tool = loader.get_tool_by_name("get_weather_openweather")
        if tool:
            print(f"  Name: {tool['name']}")
            print(f"  Category: {tool['category']}")
            print(f"  Description: {tool['description']}")
            print(f"  Substitutes: {tool.get('substitutes', [])}")
        print()

        # Test substitute query
        print("=== Substitute Tool Query ===")
        substitutes = loader.get_substitutes("get_weather_openweather")
        print(f"  Substitutes for get_weather_openweather: {substitutes}")

    except Exception as e:
        print(f"✗ Loading failed: {e}")
        import traceback
        traceback.print_exc()
