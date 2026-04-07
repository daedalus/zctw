"""Precomputed tables for CTW mathematics - using exact C tables for binary compatibility."""

import re


def _parse_c_array(content: str, array_name: str) -> list:
    """Parse a C array from header file content."""
    pattern = rf"int {array_name}\[(\w+)\] = \{{(.*?)}};"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find {array_name} in C tables")

    nums = re.findall(r"-?\d+", match.group(2))
    return [int(n) for n in nums]


# Read tables from C header
with open("/home/dclavijo/my_code/daedalus-repos/ctw/ctwmath-tables.h") as f:
    c_content = f.read()

CTWlogar = _parse_c_array(c_content, "CTWlogar")
CTWzlogpmax = _parse_c_array(c_content, "CTWzlogpmax")
CTWzlogpmin = _parse_c_array(c_content, "CTWzlogpmin")
CTWjacar = _parse_c_array(c_content, "CTWjacar")

MAXCOUNTS = len(CTWzlogpmax)
LOGENTRIES = len(CTWlogar)
JACENTRIES = len(CTWjacar)
ACCURACY = 128


def CTWjac(ent: int) -> int:
    """Jacobian logarithm lookup."""
    if -ent < JACENTRIES:
        return CTWjacar[-ent]
    return 0
