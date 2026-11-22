#!/usr/bin/env python3
"""Build CSS and flattened JSON from a Tokens Studio single-file export."""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tokens" / "tokens.json"
SITE = ROOT / "site"
OUTPUT = ROOT / "dist" / "site"
ASSETS = OUTPUT / "assets"
REFERENCE = re.compile(r"^\{([^{}]+)\}$")


class BuildError(RuntimeError):
    pass


def token_value(node: Dict[str, Any]) -> Tuple[bool, Any]:
    if "$value" in node:
        return True, node["$value"]
    if "value" in node:
        return True, node["value"]
    return False, None


def walk_tokens(
    node: Any,
    path: Tuple[str, ...],
    inherited_type: Optional[str] = None,
) -> Iterable[Dict[str, Any]]:
    if not isinstance(node, dict):
        return

    current_type = node.get("$type", node.get("type", inherited_type))
    is_token, value = token_value(node)
    if is_token:
        yield {
            "segments": path,
            "type": current_type or "unknown",
            "value": value,
            "description": node.get("$description", node.get("description")),
        }
        return

    for key, child in node.items():
        if key.startswith("$") or key in {"type", "description"}:
            continue
        yield from walk_tokens(child, path + (key,), current_type)


def normalize_reference(value: str) -> str:
    return value.strip().replace("/", ".").replace(" ", "").lower()


def css_name(parts: Iterable[str]) -> str:
    raw = "-".join(parts)
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-").lower()


def css_scalar(value: Any, token_type: str, path: Tuple[str, ...]) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        if token_type in {"dimension", "fontSize", "borderRadius"} or any(
            segment in {"space", "spacing", "radius", "size"} for segment in path
        ):
            return f"{value:g}px"
        return f"{value:g}"
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def load_tokens() -> List[Dict[str, Any]]:
    try:
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildError(f"Missing token source: {SOURCE}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(f"Invalid JSON in {SOURCE}: {exc}") from exc

    tokens: List[Dict[str, Any]] = []
    for set_name, tree in data.items():
        if set_name.startswith("$"):
            continue
        for token in walk_tokens(tree, (set_name,)):
            if len(token["segments"]) < 2:
                continue
            token["set"] = set_name
            token["path"] = token["segments"][1:]
            token["full_key"] = ".".join(token["segments"])
            token["key"] = ".".join(token["path"])
            token["css_name"] = css_name(token["path"])
            tokens.append(token)

    if not tokens:
        raise BuildError("No tokens found in the Tokens Studio export.")
    return tokens


def make_lookup(tokens: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    ambiguous = set()
    for token in tokens:
        full = normalize_reference(token["full_key"])
        short = normalize_reference(token["key"])
        lookup[full] = token
        if short in lookup and lookup[short] is not token:
            ambiguous.add(short)
        else:
            lookup[short] = token
    for key in ambiguous:
        lookup.pop(key, None)
    return lookup


def referenced_token(value: Any, lookup: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(value, str):
        return None
    match = REFERENCE.match(value.strip())
    if not match:
        return None
    key = normalize_reference(match.group(1))
    token = lookup.get(key)
    if token:
        return token

    matches = [candidate for ref, candidate in lookup.items() if ref.endswith("." + key)]
    unique = {candidate["full_key"]: candidate for candidate in matches}
    if len(unique) == 1:
        return next(iter(unique.values()))
    return None


def resolve(
    token: Dict[str, Any],
    lookup: Dict[str, Dict[str, Any]],
    trail: Optional[List[str]] = None,
) -> Any:
    trail = list(trail or [])
    if token["full_key"] in trail:
        raise BuildError("Circular token alias: " + " -> ".join(trail + [token["full_key"]]))
    target = referenced_token(token["value"], lookup)
    if not target:
        if isinstance(token["value"], str) and REFERENCE.match(token["value"].strip()):
            raise BuildError(f"Unresolved token alias {token['value']} in {token['full_key']}")
        return token["value"]
    return resolve(target, lookup, trail + [token["full_key"]])


def build_css(tokens: List[Dict[str, Any]], lookup: Dict[str, Dict[str, Any]]) -> str:
    lines = [
        "/* Generated from tokens/tokens.json. Do not edit by hand. */",
        ":root {",
    ]
    for token in tokens:
        target = referenced_token(token["value"], lookup)
        if target:
            value = f"var(--{target['css_name']})"
        else:
            value = css_scalar(token["value"], token["type"], token["path"])
        lines.append(f"  --{token['css_name']}: {value};")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def build_flattened(tokens: List[Dict[str, Any]], lookup: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    flattened: Dict[str, Any] = {}
    for token in tokens:
        key = token["key"]
        if key in flattened:
            key = token["full_key"]
        flattened[key] = {
            "$type": token["type"],
            "$value": resolve(token, lookup),
            "$original": token["value"],
            "$set": token["set"],
            "$css": f"--{token['css_name']}",
        }
        if token["description"]:
            flattened[key]["$description"] = token["description"]
    return flattened


def main() -> None:
    tokens = load_tokens()
    lookup = make_lookup(tokens)
    flattened = build_flattened(tokens, lookup)

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.copytree(SITE, OUTPUT)
    ASSETS.mkdir(parents=True, exist_ok=True)

    (ASSETS / "tokens.css").write_text(build_css(tokens, lookup), encoding="utf-8")
    (ASSETS / "flattened-tokens.json").write_text(
        json.dumps(flattened, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(SOURCE, ASSETS / "tokens.json")

    metadata = {
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "commit": os.environ.get("GITHUB_SHA", "local")[:12],
        "tokenCount": len(tokens),
        "source": "tokens/tokens.json",
    }
    (ASSETS / "build.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Built {len(tokens)} tokens into {OUTPUT}")


if __name__ == "__main__":
    try:
        main()
    except BuildError as exc:
        raise SystemExit(f"Build failed: {exc}")
