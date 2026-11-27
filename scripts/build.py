#!/usr/bin/env python3
"""Build CSS and flattened JSON from a Tokens Studio single-file export."""

from __future__ import annotations

import argparse
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
BRANDS = {"brand-a": "Core/Brand A", "brand-b": "Core/Brand B"}
PLATFORMS = {"web": "Platform/Web", "kiosk": "Platform/Kiosk", "onboard": "Platform/Onboard"}
PLATFORM_TOKENS = (
    "space.control.inline", "space.control.block", "size.control.min-width",
    "size.control.min-height", "typography.control.font-size",
    "typography.control.line-height", "focus.control.ring-width",
)
BUTTON_TOKEN = "button.primary."
STATES = ("default", "hover", "focus", "pressed")
PREVIEW_SURFACES = ("#ffffff", "#fbfafc", "#f4eff5", "#f7f6f8")


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
    if token_type == "fontFamily":
        if not isinstance(value, str) or not re.fullmatch(r"[\w -]+", value) or not value.strip():
            raise BuildError(f"Expected a single font family in {'.'.join(path)}")
        return json.dumps(value, ensure_ascii=False)
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


def load_source() -> Dict[str, Any]:
    try:
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildError(f"Missing token source: {SOURCE}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(f"Invalid JSON in {SOURCE}: {exc}") from exc

    if not isinstance(data, dict):
        raise BuildError("Expected a Tokens Studio single-file export.")
    return data


def load_tokens(data: Dict[str, Any], *sets: str) -> List[Dict[str, Any]]:
    tokens: List[Dict[str, Any]] = []
    for set_name in sets:
        tree = data.get(set_name, {} if set_name == "global" else None)
        if not isinstance(tree, dict):
            raise BuildError(f"Missing or invalid token set: {set_name}")
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
    css_names = set()
    for token in tokens:
        name = token["css_name"]
        if not name or name in css_names:
            raise BuildError(f"Duplicate or invalid CSS token name: {token['key']}")
        css_names.add(name)
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


def build_css(
    tokens: List[Dict[str, Any]], lookup: Dict[str, Dict[str, Any]], selector: str = ":root"
) -> str:
    lines = [f"{selector} {{"]
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


def luminance(value: Any) -> float:
    if not isinstance(value, str) or not re.fullmatch(r"#[a-fA-F0-9]{6}", value):
        raise BuildError(f"Button contrast checks expect opaque #RRGGBB colors, got {value!r}")
    channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))


def contrast(a: Any, b: Any) -> float:
    low, high = sorted((luminance(a), luminance(b)))
    return (high + 0.05) / (low + 0.05)


def validate_brand(brand: str, flat: Dict[str, Any]) -> None:
    font = flat.get("typography.control.font-family")
    if not font or font["$type"] != "fontFamily":
        raise BuildError(f"{brand}: missing typography.control.font-family fontFamily token")
    css_scalar(font["$value"], "fontFamily", ("typography", "control", "font-family"))

    roles = (*(f"background.{state}" for state in STATES), "text", "focus-ring")
    missing = [role for role in roles if BUTTON_TOKEN + role not in flat]
    if missing:
        raise BuildError(f"{brand}: missing button tokens: {', '.join(missing)}")
    colors = {role: flat[BUTTON_TOKEN + role]["$value"] for role in roles}
    for state in STATES:
        ratio = contrast(colors["text"], colors[f"background.{state}"])
        if ratio < 4.5:
            raise BuildError(f"{brand} {state}: label contrast {ratio:.2f}:1 is below 4.5:1")
    minimum_ring = min(contrast(colors["focus-ring"], surface) for surface in PREVIEW_SURFACES)
    if minimum_ring < 3:
        raise BuildError(f"{brand}: focus ring contrast {minimum_ring:.2f}:1 is below 3:1 on a demo surface")


def validate_platform(platform: str, flat: Dict[str, Any]) -> None:
    for name in PLATFORM_TOKENS:
        token = flat.get(name, {})
        value = token.get("$value")
        if token.get("$type") != "dimension" or not isinstance(value, str) or not re.fullmatch(r"[1-9]\d*px", value):
            raise BuildError(f"{platform}: {name} must be a positive whole-pixel dimension")


def validate_contract(sets: Dict[str, Dict[str, Any]]) -> None:
    expected = None
    for name, tokens in sets.items():
        signature = {key: (token["$type"], token["$css"]) for key, token in tokens.items()}
        if expected is not None and signature != expected:
            raise BuildError(f"{name} must expose the same token names and types as the default mode")
        expected = signature


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-storybook", action="store_true", help="Include the Storybook preview link")
    args = parser.parse_args()

    source = load_source()
    brand_outputs = {}
    for brand, token_set in BRANDS.items():
        tokens = load_tokens(source, "global", token_set, "Semantic/Value")
        lookup = make_lookup(tokens)
        flat = build_flattened(tokens, lookup)
        validate_brand(brand, flat)
        brand_outputs[brand] = (tokens, lookup, flat)

    platform_outputs = {}
    for platform, token_set in PLATFORMS.items():
        tokens = load_tokens(source, token_set)
        lookup = make_lookup(tokens)
        flat = build_flattened(tokens, lookup)
        validate_platform(platform, flat)
        platform_outputs[platform] = (tokens, lookup, flat)

    validate_contract({name: flat for name, (_, _, flat) in brand_outputs.items()})
    validate_contract({name: flat for name, (_, _, flat) in platform_outputs.items()})
    brand_flat = brand_outputs["brand-a"][2]
    platform_flat = platform_outputs["web"][2]
    overlap = {token["$css"] for token in brand_flat.values()} & {token["$css"] for token in platform_flat.values()}
    if overlap:
        raise BuildError(f"Brand and platform CSS tokens overlap: {', '.join(sorted(overlap))}")

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.copytree(SITE, OUTPUT)
    ASSETS.mkdir(parents=True, exist_ok=True)

    comment = "/* Generated from tokens/tokens.json. Do not edit by hand. */\n"
    metadata = {
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "commit": os.environ.get("GITHUB_SHA", "local")[:12],
        "tokenCount": len(brand_flat) + len(platform_flat),
        "source": "tokens/tokens.json",
        "storybook": args.with_storybook,
        "brands": list(BRANDS),
        "platforms": list(PLATFORMS),
    }
    platform_css = ""
    for platform, (tokens, lookup, _) in platform_outputs.items():
        scoped = f'[data-platform="{platform}"]'
        selector = f":root, {scoped}" if platform == "web" else scoped
        platform_css += build_css(tokens, lookup, selector)

    preview_css = comment + platform_css
    for brand, (tokens, lookup, flat) in brand_outputs.items():
        scoped = f'[data-brand="{brand}"]'
        selector = f":root, {scoped}" if brand == "brand-a" else scoped
        preview_css += build_css(tokens, lookup, selector)
        folder = ASSETS / "themes" / brand
        folder.mkdir(parents=True)
        brand_css = build_css(tokens, lookup)
        (folder / "tokens.css").write_text(comment + brand_css + platform_css, encoding="utf-8")
        shutil.copy2(SITE / "button.css", folder / "button.css")
        write_json(folder / "tokens.json", {**flat, **platform_flat})
        write_json(folder / "build.json", {**metadata, "brand": brand, "tokenSet": BRANDS[brand]})
        for platform, (platform_tokens, platform_lookup, resolved) in platform_outputs.items():
            platform_folder = folder / "platforms" / platform
            platform_folder.mkdir(parents=True)
            (platform_folder / "tokens.css").write_text(comment + brand_css + build_css(platform_tokens, platform_lookup), encoding="utf-8")
            write_json(platform_folder / "tokens.json", {**flat, **resolved})
            write_json(platform_folder / "build.json", {**metadata, "brand": brand, "platform": platform})
    (ASSETS / "tokens.css").write_text(preview_css, encoding="utf-8")
    write_json(ASSETS / "flattened-tokens.json", {**brand_flat, **platform_flat})
    write_json(ASSETS / "build.json", metadata)
    shutil.copy2(SOURCE, ASSETS / "tokens.json")
    print(f"Validated {metadata['tokenCount']} tokens across {len(BRANDS)} brands × {len(PLATFORMS)} platforms in {OUTPUT}")


if __name__ == "__main__":
    try:
        main()
    except BuildError as exc:
        raise SystemExit(f"Build failed: {exc}")
