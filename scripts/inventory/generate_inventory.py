#!/usr/bin/env python3
"""OsMEN Phase-0 inventory generator.

Generates JSON inventories under `inventory/`:
- integrations_map.json
- agents_map.json
- gateway_routes.json
- cli_commands.json
- n8n_endpoints.json
- langflow_components.json
- tools_status.json
- test_coverage.json
- hardcoded_values.json

Designed to be stdlib-only and safe to run locally.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_DIR = REPO_ROOT / "inventory"

PY_DIRS = [
    REPO_ROOT / "integrations",
    REPO_ROOT / "agents",
    REPO_ROOT / "gateway",
    REPO_ROOT / "cli_bridge",
    REPO_ROOT / "tools",
    REPO_ROOT / "scripts",
    REPO_ROOT / "tests",
]

N8N_DIR = REPO_ROOT / "n8n" / "workflows"
LANGFLOW_DIR = REPO_ROOT / "langflow" / "flows"


@dataclass
class ImportRef:
    module: str
    name: Optional[str] = None
    alias: Optional[str] = None


def _iter_py_files(base: Path) -> Iterable[Path]:
    if not base.exists():
        return
    for p in base.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        yield p


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _write_json(name: str, data: Any) -> Path:
    INVENTORY_DIR.mkdir(parents=True, exist_ok=True)
    out = INVENTORY_DIR / name
    out.write_text(
        json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    return out


def analyze_python_imports() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    for folder in PY_DIRS:
        for file_path in _iter_py_files(folder):
            rel = file_path.relative_to(REPO_ROOT).as_posix()
            src = _safe_read_text(file_path)
            try:
                tree = ast.parse(src)
            except SyntaxError as e:
                results[rel] = {"syntax_error": str(e)}
                continue

            imports: List[Dict[str, Any]] = []
            defs: List[Dict[str, Any]] = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        imports.append(asdict(ImportRef(module=a.name, alias=a.asname)))
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for a in node.names:
                        imports.append(
                            asdict(ImportRef(module=mod, name=a.name, alias=a.asname))
                        )
                elif isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    defs.append(
                        {
                            "type": node.__class__.__name__,
                            "name": node.name,
                            "lineno": getattr(node, "lineno", None),
                        }
                    )

            results[rel] = {
                "imports": imports,
                "defs": defs,
            }

    return results


_ROUTE_DECORATOR_RE = re.compile(
    r"@(router|app)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
_ROUTER_PREFIX_RE = re.compile(
    r"APIRouter\(.*?prefix\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE | re.DOTALL
)


def analyze_gateway_routes() -> Dict[str, Any]:
    routes: List[Dict[str, Any]] = []
    for file_path in _iter_py_files(REPO_ROOT / "gateway"):
        rel = file_path.relative_to(REPO_ROOT).as_posix()
        src = _safe_read_text(file_path)

        prefix = ""
        pm = _ROUTER_PREFIX_RE.search(src)
        if pm:
            prefix = pm.group(1).rstrip("/")

        for m in _ROUTE_DECORATOR_RE.finditer(src):
            decorator_target = m.group(1).lower()  # router|app
            method = m.group(2).upper()
            path = m.group(3)

            # Only router routes are affected by APIRouter(prefix=...).
            active_prefix = prefix if decorator_target == "router" else ""

            if path.startswith("/"):
                full = f"{active_prefix}{path}" if active_prefix else path
            else:
                full = f"{active_prefix}/{path}" if active_prefix else f"/{path}"

            routes.append({"file": rel, "method": method, "path": full})
    return {"routes": routes}


def analyze_cli_commands() -> Dict[str, Any]:
    cli_file = REPO_ROOT / "cli_bridge" / "osmen_cli.py"
    if not cli_file.exists():
        return {"commands": [], "error": "cli_bridge/osmen_cli.py not found"}

    src = _safe_read_text(cli_file)
    commands: Set[str] = set()

    # argparse subcommand patterns
    for m in re.finditer(r"add_parser\(\s*['\"]([^'\"]+)['\"]", src):
        commands.add(m.group(1))

    return {"commands": sorted(commands)}


def _n8n_extract_http_nodes(workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for node in workflow.get("nodes", []) or []:
        node_type = (node.get("type") or "").lower()
        if "httprequest" in node_type or node_type.endswith("httpRequest"):
            params = node.get("parameters") or {}
            url = params.get("url")
            method = params.get("method")
            out.append(
                {
                    "name": node.get("name"),
                    "type": node.get("type"),
                    "method": method,
                    "url": url,
                }
            )
    return out


def analyze_n8n_endpoints() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if not N8N_DIR.exists():
        return {"error": "n8n/workflows missing", "workflows": {}}

    for wf_path in N8N_DIR.glob("*.json"):
        rel = wf_path.relative_to(REPO_ROOT).as_posix()
        try:
            wf = json.loads(_safe_read_text(wf_path))
        except Exception as e:
            results[rel] = {"error": str(e)}
            continue

        results[rel] = {"http_nodes": _n8n_extract_http_nodes(wf)}

    return {"workflows": results}


def analyze_langflow_components() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if not LANGFLOW_DIR.exists():
        return {"error": "langflow/flows missing", "flows": {}}

    for flow_path in LANGFLOW_DIR.glob("*.json"):
        rel = flow_path.relative_to(REPO_ROOT).as_posix()
        try:
            flow = json.loads(_safe_read_text(flow_path))
        except Exception as e:
            results[rel] = {"error": str(e)}
            continue

        component_types: Set[str] = set()
        # Langflow exports vary; best-effort extraction.
        for node in flow.get("nodes", []) or []:
            t = node.get("type") or node.get("data", {}).get("type")
            if t:
                component_types.add(str(t))
        results[rel] = {"component_types": sorted(component_types)}

    return {"flows": results}


_HARDCODED_PATH_RE = re.compile(
    r"(?P<win>(?:[A-Za-z]:\\|\\\\)[^\n\r'\"]+)|(?P<posix>/(?:home|Users|var|opt|etc|tmp)/[^\n\r'\"]+)|(?P<drive>(?:[A-Za-z]:/)[^\n\r'\"]+)",
    re.IGNORECASE,
)


def analyze_hardcoded_values() -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []

    for folder in PY_DIRS:
        for file_path in _iter_py_files(folder):
            rel = file_path.relative_to(REPO_ROOT).as_posix()
            src = _safe_read_text(file_path)
            for i, line in enumerate(src.splitlines(), start=1):
                for m in _HARDCODED_PATH_RE.finditer(line):
                    findings.append(
                        {
                            "file": rel,
                            "line": i,
                            "match": m.group(0),
                        }
                    )

    return {"hardcoded_paths": findings}


def main() -> int:
    INVENTORY_DIR.mkdir(parents=True, exist_ok=True)

    imports_map = analyze_python_imports()
    _write_json("python_inventory.json", imports_map)

    _write_json("gateway_routes.json", analyze_gateway_routes())
    _write_json("cli_commands.json", analyze_cli_commands())
    _write_json("n8n_endpoints.json", analyze_n8n_endpoints())
    _write_json("langflow_components.json", analyze_langflow_components())
    _write_json("hardcoded_values.json", analyze_hardcoded_values())

    print(f"Wrote inventory JSON to: {INVENTORY_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
