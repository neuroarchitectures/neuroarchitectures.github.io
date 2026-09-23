#!/usr/bin/env python3
"""Split the NAXS specification.md into Mintlify MDX pages.

Usage:
    python3 scripts/split_spec.py [path/to/specification.md]

Re-runnable: regenerates all files under specification/. Internal anchor
links like [§25.3](#253-block-reference-components) are rewritten to
cross-page links. The Table of Contents section is dropped (Mintlify
generates navigation from docs.json).
"""

import re
import sys
import pathlib

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "../naxs/specification.md")
OUT = pathlib.Path(__file__).resolve().parent.parent / "specification"

RAW_SPEC_URL = "https://github.com/neuroarchitectures/naxs/blob/main/specification.md"

# (slug, title, description, [section keys], keep_header_block)
PAGES = [
    ("introduction", "Introduction",
     "What NAXS is and is not, its design principles, and how it relates to ONNX, PyTorch configs, and MLIR.",
     ["1", "2", "3"], True),
    ("quick-reference", "Quick Reference",
     "A one-page cheat sheet of required fields and key rules — built for agents coding against the spec.",
     ["QRC"], False),
    ("document-structure", "Document Structure",
     "Top-level JSON fields, component (node) definition, and parameter value types.",
     ["4", "5", "6"], False),
    ("operator-registry", "Operator Type Registry",
     "The 79 standard operator types — attention, convolution, normalization, MoE, and more.",
     ["7"], False),
    ("graph-model", "Graph Model",
     "Connections (edges) and scope notation — how components form a directed graph.",
     ["8", "12"], False),
    ("metadata-and-provenance", "Metadata & Provenance",
     "Vendor metadata, provenance tracking, and the extension model.",
     ["9", "10", "11"], False),
    ("validation", "Validation",
     "Structural, consistency, and parameter validation rules, plus the JSON Schema.",
     ["13", "21"], False),
    ("annotated-examples", "Annotated Examples",
     "Complete NAXS documents — minimal MLP, BERT-Base, ResNet-50, Llama-3-8B, Mamba, and 3D Gaussian Splatting.",
     ["14", "15", "16", "17", "18", "19"], False),
    ("conformance", "Conformance & Migrations",
     "Producer, consumer, and validator conformance; migration from Atlas model.json; glossary and change log.",
     ["20", "22", "23", "24"], False),
    ("block-templates", "Block Templates & Repetition",
     "Reusable subgraph definitions, block references, repeat directives, and parameter binding.",
     ["25"], False),
    ("appendices", "Appendices",
     "Standard parameter name catalog, operator frequency, scope patterns, and implementation notes.",
     ["A", "B", "C", "D", "LIC"], False),
]

section_re = re.compile(r"^## (.+)$")


def section_key(heading: str) -> str | None:
    m = re.match(r"^(\d+)\. ", heading)
    if m:
        return m.group(1)
    if heading == "Quick Reference Card":
        return "QRC"
    m = re.match(r"^Appendix ([A-D]): ", heading)
    if m:
        return m.group(1)
    if heading == "License":
        return "LIC"
    return None


def split_sections(lines: list[str]):
    """Yield (key, heading, body_lines) for every `## ` section."""
    starts = []
    for i, line in enumerate(lines):
        m = section_re.match(line)
        if m:
            starts.append((i, m.group(1).strip()))
    for idx, (start, heading) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        body = lines[start + 1:end]
        # strip trailing hr separators and blank padding
        while body and body[-1].strip() in ("---", ""):
            body.pop()
        yield section_key(heading), heading, body


def build_page_map() -> dict[str, str]:
    page_of = {}
    for slug, _, _, keys, _ in PAGES:
        for k in keys:
            page_of[k] = slug
    return page_of


def rewrite_anchors(text: str, page_of: dict[str, str]) -> str:
    def repl(m: re.Match) -> str:
        anchor = m.group(1)
        target = None
        dm = re.match(r"^(\d{1,2})", anchor)
        if dm:
            for n in (dm.group(1)[:2], dm.group(1)[:1]):
                if n in page_of:
                    target = page_of[n]
                    break
        else:
            am = re.match(r"^appendix-([a-d])", anchor)
            if am:
                target = page_of.get(am.group(1).upper())
        if target:
            return f"](/specification/{target}#{anchor})"
        return m.group(0)

    return re.sub(r"\]\(#([^)\s]+)\)", repl, text)


def main() -> None:
    raw = SRC.read_text(encoding="utf-8")
    lines = raw.replace("\r\n", "\n").split("\n")

    # header block = everything before the first `## ` heading; drop the h1
    # title line (frontmatter provides the page title) and keep the metadata
    first_h2 = next(i for i, l in enumerate(lines) if section_re.match(l))
    header_block = [l for l in lines[:first_h2] if l.strip() not in ("---", "")]
    if header_block and header_block[0].startswith("# "):
        header_block = header_block[1:]
    header_block = [l for l in header_block if l.strip() != ""]

    sections = {k: (h, b) for k, h, b in split_sections(lines) if k}
    page_of = build_page_map()

    OUT.mkdir(parents=True, exist_ok=True)

    # clean previously generated pages
    for f in OUT.glob("*.mdx"):
        f.unlink()

    for slug, title, desc, keys, keep_header in PAGES:
        parts = [f"---\ntitle: {title}\ndescription: {desc}\n---\n"]
        if keep_header:
            parts.append("> **Source of truth:** this page mirrors "
                         f"[`specification.md`]({RAW_SPEC_URL}) in the naxs repository.\n")
            parts.append("\n".join(header_block) + "\n")
        first = True
        for k in keys:
            if k not in sections:
                raise SystemExit(f"section {k!r} not found in {SRC}")
            heading, body = sections[k]
            prefix = "# " if first else "## "
            parts.append(f"\n{prefix}{heading}\n")
            parts.append("\n".join(body) + "\n")
            first = False
        text = "".join(parts)
        text = rewrite_anchors(text, page_of)
        (OUT / f"{slug}.mdx").write_text(text, encoding="utf-8")
        print(f"wrote specification/{slug}.mdx ({len(text.splitlines())} lines)")

    # verify every declared section was consumed
    used = {k for _, _, _, keys, _ in PAGES for k in keys}
    missing = set(sections) - used - {"TOC"}
    if "Table of Contents" in {h for h, _ in sections.values()} or True:
        pass  # ToC is intentionally dropped
    if missing:
        print(f"WARNING: sections not assigned to any page: {sorted(missing)}")


if __name__ == "__main__":
    main()
