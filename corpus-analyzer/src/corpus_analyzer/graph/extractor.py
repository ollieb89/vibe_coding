"""Extract relationship slugs from ## Related Skills / ## Related Files sections.

Parses the first matching section (## Related Skills or ## Related Files) and
returns a deduplicated list of slug strings.  Supports three list item formats:

* Backtick names: ``- `feature-planning`, `dev-spec` ``
* Bold names:     ``- **feature-planning**: description``
* Plain names:    ``- writing-clearly-and-concisely``
"""
from __future__ import annotations

import re

# Matches one of the two recognised section headings.
_SECTION_RE = re.compile(
    r"^## Related (?:Skills|Files)\s*\n(.*?)(?=^##|\Z)",
    re.MULTILINE | re.DOTALL,
)
# Backtick slugs: `slug-name`
_BACKTICK_RE = re.compile(r"`([a-zA-Z0-9][a-zA-Z0-9_\-\.]*)`")
# Bold slugs: **slug-name** (optionally followed by colon + description)
_BOLD_RE = re.compile(r"\*\*([a-zA-Z0-9][a-zA-Z0-9_\-\.]*)\*\*")
# Plain list item slugs: "- slug-name" with no markup, optional trailing text
_PLAIN_RE = re.compile(r"^[-*]\s+([a-zA-Z0-9][a-zA-Z0-9_\-\.]+)\s*(?:[-–].*)?$", re.MULTILINE)


def extract_related_slugs(text: str) -> list[str]:
    """Return deduplicated slugs from the first ## Related Skills/Files section.

    Args:
        text: Full Markdown file content.

    Returns:
        Ordered list of unique slug strings.  Empty list if no section found.
    """
    match = _SECTION_RE.search(text)
    if not match:
        return []

    section = match.group(1)
    seen: dict[str, None] = {}  # ordered set — preserves insertion order

    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith(("- ", "* ")):
            continue
        for slug in _BACKTICK_RE.findall(stripped):
            seen.setdefault(slug, None)
        for slug in _BOLD_RE.findall(stripped):
            if "`" not in stripped:  # don't double-count mixed lines
                seen.setdefault(slug, None)
        # Plain item: no backtick and no bold markup
        if "`" not in stripped and "**" not in stripped:
            plain = _PLAIN_RE.match(stripped)
            if plain:
                seen.setdefault(plain.group(1), None)

    return list(seen)
