#!/usr/bin/env python3
"""Build a static prompt/skill gallery from workspace sources."""

from __future__ import annotations

import json
import re
import shutil
import ssl
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path("/Users/Jay/.openclaw/workspace")
PROMPT_ROOT = ROOT / "knowledge/03-Resources/Prompt"
ATTACHMENTS = ROOT / "knowledge/attachments"
SKILL_ROOT = ROOT / "skills"
SITE = Path(__file__).resolve().parent
ASSETS = SITE / "assets/generated"


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "item"


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"\'')
    return meta, text[end + 5 :]


def title_for(path: Path, meta: dict[str, str], body: str) -> str:
    if meta.get("title"):
        return meta["title"]
    match = re.search(r"^#\s+(.+)$", body, re.M)
    if match:
        value = match.group(1).strip()
        return re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", value)
    return re.sub(r"^\d{4}-\d{2}-\d{2}[_ -]*", "", path.stem).replace("_", " ")


def plain_prompt(body: str) -> str:
    body = re.sub(r"!\[\[[^\]]+\]\]", "", body)
    body = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", body)
    body = re.sub(r"^#{1,6}\s+", "", body, flags=re.M)
    body = body.replace("```text", "").replace("```markdown", "").replace("```", "")
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def first_image(path: Path, body: str, index: int, meta: dict[str, str]) -> str | None:
    wiki = re.search(r"!\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", body)
    if wiki:
        name = wiki.group(1).strip()
        candidates = [path.parent / name, ATTACHMENTS / name, PROMPT_ROOT / "Image Prompts" / name]
        source = next((p for p in candidates if p.exists()), None)
        if source:
            target = ASSETS / f"prompt-{index:03d}-{slugify(source.stem)}{source.suffix.lower()}"
            shutil.copy2(source, target)
            return str(target.relative_to(SITE))
    configured = meta.get("thumbnail", "") or meta.get("image", "")
    remote = re.search(r"https://pbs\.twimg\.com/(?:media|amplify_video_thumb)/[^\s\)\]]+", configured or body)
    if remote:
        url = remote.group(0).rstrip('"\'.,')
        target = ASSETS / f"prompt-{index:03d}-remote.jpg"
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=20, context=ssl._create_unverified_context()) as response:
                target.write_bytes(response.read())
            return str(target.relative_to(SITE))
        except Exception:
            return url
    return None


def build_prompts() -> list[dict]:
    items = []
    paths = sorted(PROMPT_ROOT.rglob("*.md"), key=lambda p: p.name.casefold())
    for index, path in enumerate(paths, 1):
        raw = path.read_text(encoding="utf-8", errors="replace")
        meta, body = frontmatter(raw)
        title = title_for(path, meta, body)
        content = plain_prompt(body)
        category = "Image" if ("image" in str(path).lower() or "이미지" in raw[:500] or "poster" in raw[:500].lower()) else "Prompt"
        items.append({
            "id": f"prompt-{index}",
            "title": title,
            "category": category,
            "image": first_image(path, body, index, meta),
            "content": content,
            "source": meta.get("source", ""),
            "path": str(path.relative_to(ROOT)),
        })
    return sorted(items, key=lambda item: (item["image"] is None, item["title"].casefold()))


def build_skills() -> list[dict]:
    items = []
    paths = sorted(
        SKILL_ROOT.glob("*/SKILL.md"),
        key=lambda path: (-path.stat().st_mtime_ns, path.parent.name.casefold()),
    )
    for index, path in enumerate(paths, 1):
        raw = path.read_text(encoding="utf-8", errors="replace")
        meta, body = frontmatter(raw)
        title = meta.get("name") or path.parent.name
        description = meta.get("description", "").replace(">", "").strip()
        if not description:
            paragraph = re.search(r"\n([^#\n][^\n]{20,})", body)
            description = paragraph.group(1).strip() if paragraph else ""
        homepage = meta.get("homepage", "")
        items.append({
            "id": f"skill-{index}",
            "title": title,
            "description": description,
            # The hub shows a usable summary, not private operating instructions.
            "content": description,
            "link": homepage,
            "path": str(path.relative_to(ROOT)),
        })
    return items


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for old in ASSETS.iterdir():
        if old.is_file():
            old.unlink()
    payload = {"prompts": build_prompts(), "skills": build_skills()}
    (SITE / "data.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"Built {len(payload['prompts'])} prompts and {len(payload['skills'])} skills")


if __name__ == "__main__":
    main()
