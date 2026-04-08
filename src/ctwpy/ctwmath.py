"""Precomputed tables for CTW mathematics - using exact C tables for binary compatibility."""

from ctwpy._tables import CTWLOGAR, CTWZLOGPMAX, CTWZLOGPMIN, CTWJACAR

CTWlogar = CTWLOGAR
CTWzlogpmax = CTWZLOGPMAX
CTWzlogpmin = CTWZLOGPMIN
CTWjacar = CTWJACAR

MAXCOUNTS = len(CTWzlogpmax)
LOGENTRIES = len(CTWlogar)
JACENTRIES = len(CTWjacar)
ACCURACY = 128


def CTWjac(ent: int) -> int:
    """Jacobian logarithm lookup."""
    if -ent < JACENTRIES:
        return CTWjacar[-ent]
    return 0
