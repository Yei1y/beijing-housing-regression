"""Strip comments and docstrings from project Python scripts for the appendix."""

import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT_DIR = PROJECT_ROOT / "scripts"
OUT_DIR = PROJECT_ROOT / "report" / "code"

files = [
    "utils.py",
    "00_descriptive_table.py",
    "01_exploratory.py",
    "02_preprocessing.py",
    "03_variable_selection.py",
    "04_model_diagnostics.py",
    "05_model_comparison.py",
]

def strip_py(source: str) -> str:
    """Remove comments and docstrings from Python source."""
    lines = source.split("\n")
    out = []
    in_triple = False

    for line in lines:
        stripped = line.strip()

        # Handle triple-quoted docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            count = stripped.count(stripped[:3])
            if count >= 2:
                continue  # one-line docstring
            in_triple = not in_triple
            continue

        if in_triple:
            if stripped.endswith('"""') or stripped.endswith("'''"):
                in_triple = False
            continue

        # Strip inline comments (but not inside strings)
        # Simple approach: find # not inside quotes, strip from there
        in_single = False
        in_double = False
        comment_pos = -1
        for i, ch in enumerate(line):
            if ch == '"' and (i == 0 or line[i - 1] != "\\"):
                in_double = not in_double
            elif ch == "'" and (i == 0 or line[i - 1] != "\\"):
                in_single = not in_single
            elif ch == "#" and not in_single and not in_double:
                comment_pos = i
                break

        if comment_pos >= 0:
            line = line[:comment_pos]

        stripped = line.strip()
        if stripped == "":
            continue

        out.append(line)

    # Remove consecutive blank lines
    result = []
    prev_empty = False
    for line in out:
        empty = line.strip() == ""
        if empty and prev_empty:
            continue
        result.append(line)
        prev_empty = empty

    return "\n".join(result)

for fname in files:
    src_path = SCRIPT_DIR / fname if fname != "utils.py" else PROJECT_ROOT / "utils.py"
    if not src_path.exists():
        print(f"SKIP: {src_path} not found")
        continue

    src = src_path.read_text(encoding="utf-8")
    clean = strip_py(src)
    clean = clean.rstrip() + "\n"

    out_path = OUT_DIR / fname
    out_path.write_text(clean, encoding="utf-8")
    orig_lines = len(src.split("\n"))
    clean_lines = len(clean.split("\n"))
    print(f"{fname}: {orig_lines} -> {clean_lines} lines ({orig_lines - clean_lines} removed)")

print(f"\nDone. Stripped files saved to {OUT_DIR}")
