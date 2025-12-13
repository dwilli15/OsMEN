#!/usr/bin/env python3
"""Check n8n workflow HTTP calls against gateway routes.

Reads:
- inventory/gateway_routes.json
- inventory/n8n_endpoints.json

Writes:
- inventory/n8n_gateway_coherence.json

Best-effort:
- Normalizes URLs (including n8n "expression" URLs prefixed with '=')
- Classifies calls by target service (gateway/langflow/mcp/etc)
- Only compares calls targeting the gateway (host=localhost/gateway, port=8080)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_DIR = REPO_ROOT / "inventory"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _strip_n8n_expression_prefix(url: str) -> str:
    # n8n can represent literal URLs as expressions like "=http://...".
    # Treat those as plain URLs for parsing.
    u = url.strip()
    if u.startswith("="):
        return u[1:].lstrip()
    return u


def _parse_url(
    url: Optional[str],
) -> Optional[Tuple[Optional[str], Optional[int], str]]:
    """Return (host, port, path) for a URL or path-like string."""
    if not url:
        return None
    try:
        cleaned = _strip_n8n_expression_prefix(url)
        p = urlparse(cleaned)
        if p.scheme and p.netloc:
            return p.hostname, p.port, p.path or "/"
        # Might already be a path
        path = cleaned
        if not path.startswith("/"):
            path = f"/{path}"
        return None, None, path
    except Exception:
        return None


def _classify_target(host: Optional[str], port: Optional[int], path: str) -> str:
    host_l = (host or "").lower()
    if host_l in {"gateway", "localhost", "127.0.0.1", "host.docker.internal"}:
        if port in (None, 8080):
            return "gateway"
    if port == 7860 or "langflow" in host_l:
        return "langflow"
    if port == 8081 or host_l == "mcp-server":
        return "mcp"
    if port == 3000 or "convertx" in host_l:
        return "convertx"
    if port == 8000 or "chromadb" in host_l:
        return "chromadb"
    if port == 8200 or "qdrant" in host_l:
        return "vector"
    # Heuristic: relative /api/* usually targets gateway.
    if host is None and path.startswith("/api/"):
        return "gateway"
    return "other"


def _normalize_method(method: Optional[str]) -> str:
    return (method or "GET").upper()


def main() -> int:
    routes_path = INVENTORY_DIR / "gateway_routes.json"
    n8n_path = INVENTORY_DIR / "n8n_endpoints.json"

    if not routes_path.exists() or not n8n_path.exists():
        raise SystemExit("Run scripts/inventory/generate_inventory.py first")

    routes_json = _load_json(routes_path)
    n8n_json = _load_json(n8n_path)

    route_set: Set[Tuple[str, str]] = set()
    for r in routes_json.get("routes", []):
        route_set.add((_normalize_method(r.get("method")), r.get("path") or ""))

    gateway_missing: List[Dict[str, Any]] = []
    gateway_matched: List[Dict[str, Any]] = []
    non_gateway_calls: Dict[str, List[Dict[str, Any]]] = {}

    workflows = n8n_json.get("workflows") or {}
    for wf_file, wf_data in workflows.items():
        for node in wf_data.get("http_nodes", []) or []:
            method = _normalize_method(node.get("method"))
            parsed = _parse_url(node.get("url"))
            if not parsed:
                gateway_missing.append(
                    {
                        "workflow": wf_file,
                        "node": node.get("name"),
                        "reason": "missing_url",
                        "method": method,
                        "url": node.get("url"),
                    }
                )
                continue

            host, port, path = parsed
            target = _classify_target(host, port, path)
            if target != "gateway":
                non_gateway_calls.setdefault(target, []).append(
                    {
                        "workflow": wf_file,
                        "node": node.get("name"),
                        "method": method,
                        "host": host,
                        "port": port,
                        "path": path,
                        "url": node.get("url"),
                    }
                )
                continue

            key = (method, path)
            if key in route_set:
                gateway_matched.append(
                    {
                        "workflow": wf_file,
                        "node": node.get("name"),
                        "method": method,
                        "path": path,
                    }
                )
            else:
                gateway_missing.append(
                    {
                        "workflow": wf_file,
                        "node": node.get("name"),
                        "method": method,
                        "path": path,
                        "url": node.get("url"),
                    }
                )

    out = {
        "gateway_matched": gateway_matched,
        "gateway_missing": gateway_missing,
        "non_gateway_calls": non_gateway_calls,
        "route_count": len(route_set),
        "n8n_http_node_count": sum(
            len((wf_data.get("http_nodes") or [])) for wf_data in workflows.values()
        ),
    }

    out_path = INVENTORY_DIR / "n8n_gateway_coherence.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote: {out_path}")

    if gateway_missing:
        print(f"Gateway-missing routes: {len(gateway_missing)}")
    else:
        print("All gateway-targeted n8n HTTP calls match gateway routes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
