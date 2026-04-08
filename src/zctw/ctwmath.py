"""Precomputed tables for CTW mathematics - using exact C tables for binary compatibility."""

from zctw._tables import CTWJACAR, CTWLOGAR, CTWZLOGPMAX, CTWZLOGPMIN

CTWlogar = CTWLOGAR
CTWzlogpmax = CTWZLOGPMAX
CTWzlogpmin = CTWZLOGPMIN
CTWjacar = CTWJACAR

MAXCOUNTS = len(CTWzlogpmax)
LOGENTRIES = len(CTWlogar)
JACENTRIES = len(CTWjacar)
ACCURACY = 128

# Try to use Cython-accelerated CTWjac
try:
    import zctw._cython_ctw as _cython_mod

    _cython_mod.init_cython()
    _CTWjac_cython = _cython_mod.ctw_jac

    def CTWjac(ent: int) -> int:
        """Jacobian logarithm lookup (Cython-accelerated)."""
        if -ent < JACENTRIES:
            return _CTWjac_cython(ent)
        return 0
except (ImportError, AttributeError):

    def CTWjac(ent: int) -> int:
        """Jacobian logarithm lookup."""
        if -ent < JACENTRIES:
            return CTWjacar[-ent]
        return 0
