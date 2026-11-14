#!/usr/bin/env python3
"""Build a PR tour page: tour.json + the PR's unified diff -> one HTML file.

Usage: build.py tour.json pr.diff out.html

Each step's `hunks` lists {file, start, end} in new-file line numbers; the
diff lines for that range are cut from pr.diff, so the page never shows
hand-copied code. Exits 1 if a diff file is in no step, or a hunk is empty.
"""
import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).with_name("template.html")


def parse_diff(text):
    """{path: [(kind, text, anchor_new_line)]}; '-' lines anchor to the next new line."""
    files, path, old, new_no = {}, None, None, 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            path = None
        elif line.startswith("--- "):
            old = line[6:] if line.startswith("--- a/") else None
        elif line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            files[path or old] = []  # deleted file: listed, no new lines
        elif path and line.startswith("@@"):
            new_no = int(re.match(r"@@ -\S+ \+(\d+)", line).group(1))
            files[path].append(("@", line, new_no))
        elif path and line[:1] in "+ ":
            files[path].append((line[:1], line[1:], new_no))
            new_no += 1
        elif path and line[:1] == "-":
            files[path].append(("-", line[1:], new_no))
    return files


def cut(lines, start, end):
    return [
        {"k": k, "t": t, "n": n if k != "-" else None}
        for k, t, n in lines
        if k != "@" and start <= n <= end
    ]


def main(tour_path, diff_path, out_path):
    tour = json.loads(Path(tour_path).read_text())
    diff = parse_diff(Path(diff_path).read_text())
    problems, covered = [], set()
    for step in tour["steps"]:
        covered.update(f["path"] for f in step.get("files", []))
        for h in step.get("hunks", []):
            lines = cut(diff.get(h["file"], []), h["start"], h["end"])
            if not lines:
                problems.append(f"empty hunk: {h['file']} {h['start']}-{h['end']}")
            h["lines"] = lines
    problems += [f"file in no step: {p}" for p in sorted(set(diff) - covered)]
    data = json.dumps(tour, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text().replace("/*TOUR_DATA*/null", data, 1)
    html = html.replace("<title>PR tour</title>", f"<title>PR {tour['pr']['number']} tour</title>", 1)
    Path(out_path).write_text(html)
    for p in problems:
        print(p, file=sys.stderr)
    print(f"wrote {out_path}: {len(tour['steps'])} steps, {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main(*sys.argv[1:4])
