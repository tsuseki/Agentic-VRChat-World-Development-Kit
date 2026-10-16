#!/usr/bin/env python3
"""Group Frame Debugger draw events by object category.

Input: a JSON list of events, one object per event, with at least
  {"type": "Mesh|StaticBatch|InstancedMesh|DynamicGeometry|...", "path": "Root/Child/Leaf" or null}
(see references/draw-call-attribution.md for how to capture it).

Usage:
  draw_categories.py events.json [--rules rules.json] [--split CATEGORY] [--json out.json]

Rules: JSON list of [category, regex] pairs matched against the hierarchy path, first match wins.
The defaults below are generic; adapt names per world with --rules.
"""
import argparse
import collections
import json
import re
import sys

DRAW_TYPES = {"Mesh", "StaticBatch", "InstancedMesh", "DynamicGeometry"}

DEFAULT_RULES = [
    ["Games (Udon tables, pens)", r"Poker|Holdem|Mahjong|Billiard|VRCSA|QvPen|Chess|Darts"],
    ["Video & screens", r"VizVid|ProTV|USharpVideo|VIDEO|Screen"],
    ["UI & panels", r"Canvas|SETTINGS|Panel|Sign|Menu"],
    ["Window frames & mullions", r"Mullion|Sill|Transom|SlidingLeaf.*Frame|Glazing.*(Frame|Post|Head)"],
    ["Glass panes", r"GlassFace|Window_Glass"],
    ["Railings & guards", r"Guard|Handrail|Railing|Baluster|MidRail|TopRail|Newel|/Rail/"],
    ["Glass panes", r"Glazing|Glass(?!ware)"],
    ["Gym equipment", r"Gym|Cardio|Treadmill|Elliptical|Rower|DenseRack|Weights|Dumbbell|LegPress|LegExtension|Strength"],
    ["Electronics & services", r"AC_Unit|Smoke|Vent|Outlet|Switch|/Services|Server|VRGear|Battlestation|Monitor|Console|TV|Gamepad|Printer"],
    ["Pictures & art", r"ARTWORK|Artwork|/ART/|Painting|Picture(?!Light)|Statue|Sculpture"],
    ["Light fixtures", r"Light|Lamp|Pendant|Sconce|Diffuser|Uplight|Bollard|Flood|LED|Cove|Lens|Trim"],
    ["Plants & trees", r"Plant|Pot|Tropical|Bush|Tree|Hedge|Fern|Leaf|Leaves|Foliage|Planter"],
    ["Water", r"Water|Pool|Jacuzzi|Spa"],
    ["Books & shelves", r"Book|Shelf|Shelves"],
    ["Bottles & small dressing", r"Bottle|Wine|Glassware|Cup|Mug|Vase|Bowl|Tray|Clutter"],
    ["Built-ins (bar, kitchen, bath)", r"Bar|Kitchen|Counter|Sink|Shower|Vanity|Bath|Fireplace"],
    ["Furniture", r"Furniture|Sofa|Couch|Chair|Table|Stool|Bed|Bench|Desk|Cabinet|Credenza|Pillow|Rug"],
    ["Walls, floors, stairs", r"^SHELL|^SITE|Wall|Floor|Ceiling|Stair|Column|Slab|Roof|Tile"],
    ["Other", r"."],
]


def load_rules(path):
    if not path:
        return [(n, re.compile(r)) for n, r in DEFAULT_RULES]
    with open(path, encoding="utf-8") as f:
        return [(n, re.compile(r)) for n, r in json.load(f)]


def categorize(path, rules):
    for name, rx in rules:
        if rx.search(path):
            return name
    return "Other"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("events")
    ap.add_argument("--rules")
    ap.add_argument("--split", help="drill into one category by its first three path segments")
    ap.add_argument("--json", dest="out")
    ap.add_argument("--examples", type=int, default=3)
    a = ap.parse_args()

    with open(a.events, encoding="utf-8") as f:
        events = json.load(f)
    if isinstance(events, dict):
        events = events.get("events", [])
    rules = load_rules(a.rules)

    counts = collections.Counter()
    examples = collections.defaultdict(list)
    split = collections.Counter()
    for e in events:
        if e.get("type") not in DRAW_TYPES:
            continue
        path = e.get("path")
        if not path:
            key = "(static batches, not attributable)" if e.get("type") == "StaticBatch" else "(engine: skybox, post, unnamed)"
        else:
            key = categorize(path, rules)
            if a.split and key == a.split:
                split["/".join(path.split("/")[:3])] += 1
        counts[key] += 1
        if path and len(examples[key]) < a.examples and path not in examples[key]:
            examples[key].append(path)

    total = sum(counts.values())
    print(f"draw events: {total}")
    print(f"| category | events | % | examples |\n|---|---:|---:|---|")
    for k, v in counts.most_common():
        print(f"| {k} | {v} | {100 * v / total:.1f} | {'; '.join(examples.get(k, []))} |")
    if a.split:
        print(f"\n{a.split} by sub-path:")
        for k, v in split.most_common():
            print(f"{v:6d}  {k}")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump({"total": total, "categories": counts.most_common(), "examples": examples,
                       "split": split.most_common() if a.split else None}, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
