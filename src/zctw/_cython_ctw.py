"""Cython-optimized CTW math module.

This module provides fast implementations of CTW math operations using Cython.
If Cython is not available, falls back to pure Python implementation.
"""

try:
    from zctw._cython_ctw import init_cython, ctw_jac, ctw_process_wrapper

    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False
    ctw_jac = None
    ctw_process_wrapper = None


def get_ctwjac():
    """Return the CTWjac function (Cython if available, else pure Python)."""
    if CYTHON_AVAILABLE:
        return ctw_jac
    from zctw.ctwmath import CTWjac

    return CTWjac


def get_ctw_process():
    """Return the ctw_process function (Cython if available, else pure Python)."""
    return ctw_process_wrapper


def init():
    """Initialize Cython tables if available. Returns True if Cython is active."""
    if CYTHON_AVAILABLE:
        init_cython()
        return True
    return False
