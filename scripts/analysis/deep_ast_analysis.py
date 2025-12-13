#!/usr/bin/env python3
"""
PHOENIX Protocol - Deep AST Analysis
=====================================

Phase 0 Reconnaissance: Line-by-line analysis of every Python file.

Generates:
- Import dependency graph
- Dead code detection
- Circular dependency identification
- Complexity metrics
- Type hint coverage
- Docstring coverage
"""

import ast
import json
import os
import sys
import traceback
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class FunctionAnalysis:
    """Analysis of a single function/method."""

    name: str
    lineno: int
    end_lineno: int
    args_count: int
    has_return_type: bool
    has_docstring: bool
    complexity: int  # Cyclomatic complexity estimate
    local_vars: int
    nested_depth: int
    calls: List[str] = field(default_factory=list)
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)


@dataclass
class ClassAnalysis:
    """Analysis of a single class."""

    name: str
    lineno: int
    end_lineno: int
    has_docstring: bool
    methods: List[FunctionAnalysis] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    class_vars: int = 0
    instance_vars: int = 0


@dataclass
class FileAnalysis:
    """Complete analysis of a Python file."""

    path: str
    lines_total: int
    lines_code: int
    lines_comment: int
    lines_blank: int

    # Imports
    imports: List[str] = field(default_factory=list)
    from_imports: Dict[str, List[str]] = field(default_factory=dict)

    # Definitions
    functions: List[FunctionAnalysis] = field(default_factory=list)
    classes: List[ClassAnalysis] = field(default_factory=list)
    global_vars: List[str] = field(default_factory=list)

    # Quality metrics
    has_module_docstring: bool = False
    type_hint_coverage: float = 0.0
    docstring_coverage: float = 0.0
    avg_complexity: float = 0.0
    max_complexity: int = 0

    # Issues
    syntax_errors: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)
    unused_imports: List[str] = field(default_factory=list)

    # Dependencies
    internal_deps: List[str] = field(default_factory=list)  # OsMEN modules
    external_deps: List[str] = field(default_factory=list)  # Third-party


class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity."""

    def __init__(self):
        self.complexity = 1  # Base complexity

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds a branch
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node):
        self.complexity += 1
        self.generic_visit(node)


class CallCollector(ast.NodeVisitor):
    """Collect all function calls in a node."""

    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.append(node.func.attr)
        self.generic_visit(node)


class FileAnalyzer:
    """Analyze a single Python file."""

    def __init__(self, filepath: Path, repo_root: Path):
        self.filepath = filepath
        self.repo_root = repo_root
        self.content = ""
        self.lines = []
        self.tree = None

    def analyze(self) -> FileAnalysis:
        """Perform complete analysis of the file."""
        analysis = FileAnalysis(
            path=str(self.filepath.relative_to(self.repo_root)),
            lines_total=0,
            lines_code=0,
            lines_comment=0,
            lines_blank=0,
        )

        try:
            self.content = self.filepath.read_text(encoding="utf-8", errors="replace")
            self.lines = self.content.splitlines()
        except Exception as e:
            analysis.syntax_errors.append(f"Read error: {e}")
            return analysis

        # Line counts
        analysis.lines_total = len(self.lines)
        for line in self.lines:
            stripped = line.strip()
            if not stripped:
                analysis.lines_blank += 1
            elif stripped.startswith("#"):
                analysis.lines_comment += 1
            else:
                analysis.lines_code += 1

        # Parse AST
        try:
            self.tree = ast.parse(self.content)
        except SyntaxError as e:
            analysis.syntax_errors.append(f"Line {e.lineno}: {e.msg}")
            return analysis

        # Module docstring
        if (
            self.tree.body
            and isinstance(self.tree.body[0], ast.Expr)
            and isinstance(self.tree.body[0].value, ast.Constant)
            and isinstance(self.tree.body[0].value.value, str)
        ):
            analysis.has_module_docstring = True

        # Analyze imports
        self._analyze_imports(analysis)

        # Analyze definitions
        self._analyze_definitions(analysis)

        # Calculate coverage metrics
        self._calculate_metrics(analysis)

        return analysis

    def _analyze_imports(self, analysis: FileAnalysis):
        """Extract all imports from the AST."""
        osmen_modules = {
            "integrations",
            "agents",
            "tools",
            "gateway",
            "cli_bridge",
            "parsers",
            "scheduling",
            "workflows",
            "day1",
            "osmen",
        }

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    analysis.imports.append(alias.name)
                    if module in osmen_modules:
                        analysis.internal_deps.append(alias.name)
                    else:
                        analysis.external_deps.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_root = node.module.split(".")[0]
                    names = [alias.name for alias in node.names]
                    analysis.from_imports[node.module] = names

                    if module_root in osmen_modules:
                        analysis.internal_deps.append(node.module)
                    else:
                        analysis.external_deps.append(node.module)

    def _analyze_definitions(self, analysis: FileAnalysis):
        """Analyze all function and class definitions."""
        for node in self.tree.body:
            if isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
                func = self._analyze_function(node)
                analysis.functions.append(func)

            elif isinstance(node, ast.ClassDef):
                cls = self._analyze_class(node)
                analysis.classes.append(cls)

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        analysis.global_vars.append(target.id)

    def _analyze_function(self, node) -> FunctionAnalysis:
        """Analyze a single function/method."""
        # Check for docstring
        has_docstring = (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        )

        # Check return type
        has_return_type = node.returns is not None

        # Calculate complexity
        cv = ComplexityVisitor()
        cv.visit(node)

        # Collect calls
        cc = CallCollector()
        cc.visit(node)

        # Count local variables
        local_vars = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                local_vars += len(child.targets)

        # Get decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)

        return FunctionAnalysis(
            name=node.name,
            lineno=node.lineno,
            end_lineno=getattr(node, "end_lineno", node.lineno),
            args_count=len(node.args.args),
            has_return_type=has_return_type,
            has_docstring=has_docstring,
            complexity=cv.complexity,
            local_vars=local_vars,
            nested_depth=0,  # TODO: Calculate nesting
            calls=cc.calls,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            decorators=decorators,
        )

    def _analyze_class(self, node: ast.ClassDef) -> ClassAnalysis:
        """Analyze a single class."""
        # Check for docstring
        has_docstring = (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        )

        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)

        # Analyze methods
        methods = []
        class_vars = 0
        instance_vars = set()

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._analyze_function(item))

                # Count instance variables from __init__
                if item.name == "__init__":
                    for child in ast.walk(item):
                        if isinstance(child, ast.Assign):
                            for target in child.targets:
                                if (
                                    isinstance(target, ast.Attribute)
                                    and isinstance(target.value, ast.Name)
                                    and target.value.id == "self"
                                ):
                                    instance_vars.add(target.attr)

            elif isinstance(item, ast.Assign):
                class_vars += len(item.targets)

        return ClassAnalysis(
            name=node.name,
            lineno=node.lineno,
            end_lineno=getattr(node, "end_lineno", node.lineno),
            has_docstring=has_docstring,
            methods=methods,
            bases=bases,
            class_vars=class_vars,
            instance_vars=len(instance_vars),
        )

    def _calculate_metrics(self, analysis: FileAnalysis):
        """Calculate aggregate quality metrics."""
        # Type hint coverage
        total_funcs = len(analysis.functions)
        for cls in analysis.classes:
            total_funcs += len(cls.methods)

        if total_funcs > 0:
            typed_funcs = sum(1 for f in analysis.functions if f.has_return_type)
            for cls in analysis.classes:
                typed_funcs += sum(1 for m in cls.methods if m.has_return_type)
            analysis.type_hint_coverage = typed_funcs / total_funcs

        # Docstring coverage
        total_items = total_funcs + len(analysis.classes)
        if analysis.has_module_docstring:
            total_items += 1

        if total_items > 0:
            documented = 1 if analysis.has_module_docstring else 0
            documented += sum(1 for f in analysis.functions if f.has_docstring)
            documented += sum(1 for c in analysis.classes if c.has_docstring)
            for cls in analysis.classes:
                documented += sum(1 for m in cls.methods if m.has_docstring)
                total_items += len(cls.methods)
            analysis.docstring_coverage = documented / total_items

        # Complexity metrics
        all_complexities = [f.complexity for f in analysis.functions]
        for cls in analysis.classes:
            all_complexities.extend(m.complexity for m in cls.methods)

        if all_complexities:
            analysis.avg_complexity = sum(all_complexities) / len(all_complexities)
            analysis.max_complexity = max(all_complexities)


def analyze_directory(directory: Path, repo_root: Path) -> List[FileAnalysis]:
    """Analyze all Python files in a directory."""
    results = []

    for py_file in directory.rglob("*.py"):
        # Skip virtual environments and cache
        if any(
            part in py_file.parts
            for part in [".venv", "__pycache__", "node_modules", ".git"]
        ):
            continue

        analyzer = FileAnalyzer(py_file, repo_root)
        analysis = analyzer.analyze()
        results.append(analysis)

    return results


def build_dependency_graph(analyses: List[FileAnalysis]) -> Dict[str, List[str]]:
    """Build a dependency graph from file analyses."""
    graph = {}

    for analysis in analyses:
        deps = set(analysis.internal_deps)
        graph[analysis.path] = list(deps)

    return graph


def find_circular_dependencies(graph: Dict[str, List[str]]) -> List[List[str]]:
    """Find circular dependencies using DFS."""
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            # Normalize the neighbor path
            for potential_match in graph.keys():
                if neighbor in potential_match or potential_match.endswith(
                    neighbor.replace(".", "/") + ".py"
                ):
                    if potential_match in rec_stack:
                        # Found cycle
                        cycle_start = path.index(potential_match)
                        cycles.append(path[cycle_start:] + [potential_match])
                    elif potential_match not in visited:
                        dfs(potential_match)
                    break

        path.pop()
        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def generate_report(analyses: List[FileAnalysis], output_path: Path):
    """Generate a comprehensive analysis report."""
    report = {
        "summary": {
            "total_files": len(analyses),
            "total_lines": sum(a.lines_total for a in analyses),
            "total_code_lines": sum(a.lines_code for a in analyses),
            "total_functions": sum(len(a.functions) for a in analyses),
            "total_classes": sum(len(a.classes) for a in analyses),
            "files_with_syntax_errors": sum(1 for a in analyses if a.syntax_errors),
            "avg_type_hint_coverage": (
                sum(a.type_hint_coverage for a in analyses) / len(analyses)
                if analyses
                else 0
            ),
            "avg_docstring_coverage": (
                sum(a.docstring_coverage for a in analyses) / len(analyses)
                if analyses
                else 0
            ),
        },
        "high_complexity_functions": [],
        "files_without_docstrings": [],
        "syntax_errors": [],
        "dependency_graph": {},
        "circular_dependencies": [],
        "files": [],
    }

    # Find high complexity functions (>10)
    for analysis in analyses:
        for func in analysis.functions:
            if func.complexity > 10:
                report["high_complexity_functions"].append(
                    {
                        "file": analysis.path,
                        "function": func.name,
                        "complexity": func.complexity,
                        "line": func.lineno,
                    }
                )
        for cls in analysis.classes:
            for method in cls.methods:
                if method.complexity > 10:
                    report["high_complexity_functions"].append(
                        {
                            "file": analysis.path,
                            "class": cls.name,
                            "method": method.name,
                            "complexity": method.complexity,
                            "line": method.lineno,
                        }
                    )

    # Files without module docstrings
    for analysis in analyses:
        if not analysis.has_module_docstring and analysis.lines_code > 50:
            report["files_without_docstrings"].append(analysis.path)

    # Syntax errors
    for analysis in analyses:
        if analysis.syntax_errors:
            report["syntax_errors"].append(
                {
                    "file": analysis.path,
                    "errors": analysis.syntax_errors,
                }
            )

    # Build dependency graph
    report["dependency_graph"] = build_dependency_graph(analyses)

    # Find circular dependencies
    report["circular_dependencies"] = find_circular_dependencies(
        report["dependency_graph"]
    )

    # Convert analyses to dicts (just summaries to keep file size reasonable)
    for analysis in analyses:
        report["files"].append(
            {
                "path": analysis.path,
                "lines": analysis.lines_total,
                "code_lines": analysis.lines_code,
                "functions": len(analysis.functions),
                "classes": len(analysis.classes),
                "type_hint_coverage": round(analysis.type_hint_coverage, 2),
                "docstring_coverage": round(analysis.docstring_coverage, 2),
                "max_complexity": analysis.max_complexity,
                "internal_deps": analysis.internal_deps,
                "external_deps": analysis.external_deps[:10],  # Limit to top 10
                "has_errors": bool(analysis.syntax_errors),
            }
        )

    # Sort high complexity by complexity descending
    report["high_complexity_functions"].sort(
        key=lambda x: x["complexity"], reverse=True
    )

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def main():
    """Run the deep AST analysis."""
    repo_root = Path(__file__).parent.parent.parent
    output_dir = repo_root / ".refactor"

    print("=" * 60)
    print("PHOENIX Protocol - Deep AST Analysis")
    print("=" * 60)
    print(f"\nRepository: {repo_root}")
    print(f"Output: {output_dir}")

    # Analyze all Python files
    print("\n[1/4] Scanning Python files...")
    analyses = analyze_directory(repo_root, repo_root)
    print(f"      Found {len(analyses)} Python files")

    # Generate report
    print("\n[2/4] Analyzing AST structures...")
    report = generate_report(analyses, output_dir / "ast_analysis.json")

    # Print summary
    print("\n[3/4] Summary:")
    print(f"      Total files: {report['summary']['total_files']}")
    print(f"      Total lines: {report['summary']['total_lines']:,}")
    print(f"      Code lines: {report['summary']['total_code_lines']:,}")
    print(f"      Functions: {report['summary']['total_functions']}")
    print(f"      Classes: {report['summary']['total_classes']}")
    print(f"      Syntax errors: {report['summary']['files_with_syntax_errors']}")
    print(f"      Avg type coverage: {report['summary']['avg_type_hint_coverage']:.1%}")
    print(
        f"      Avg docstring coverage: {report['summary']['avg_docstring_coverage']:.1%}"
    )

    # Print issues
    print("\n[4/4] Issues Found:")

    if report["syntax_errors"]:
        print(f"\n   ❌ SYNTAX ERRORS ({len(report['syntax_errors'])} files):")
        for err in report["syntax_errors"][:10]:
            print(f"      - {err['file']}: {err['errors'][0]}")

    if report["high_complexity_functions"]:
        print(
            f"\n   ⚠️  HIGH COMPLEXITY (>{10}) ({len(report['high_complexity_functions'])} functions):"
        )
        for item in report["high_complexity_functions"][:10]:
            if "class" in item:
                print(
                    f"      - {item['file']}:{item['line']} {item['class']}.{item['method']} (complexity={item['complexity']})"
                )
            else:
                print(
                    f"      - {item['file']}:{item['line']} {item['function']} (complexity={item['complexity']})"
                )

    if report["circular_dependencies"]:
        print(
            f"\n   🔄 CIRCULAR DEPENDENCIES ({len(report['circular_dependencies'])} cycles):"
        )
        for cycle in report["circular_dependencies"][:5]:
            print(f"      - {' → '.join(cycle[:4])}...")

    if report["files_without_docstrings"]:
        print(
            f"\n   📝 MISSING MODULE DOCSTRINGS ({len(report['files_without_docstrings'])} files):"
        )
        for path in report["files_without_docstrings"][:10]:
            print(f"      - {path}")

    print("\n" + "=" * 60)
    print(f"Full report: {output_dir / 'ast_analysis.json'}")
    print("=" * 60)

    return 0 if not report["syntax_errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
