# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

"""Cython-optimized CTW math operations - compiled module."""

cimport cython
from libc.stdlib cimport malloc, free
from libc.string cimport memset, memcpy

cdef int EMPTY_NODE = 0xFFFFFFFF

# SHIFT_MASK as C array for fast access
cdef int SHIFT_MASK[8]
SHIFT_MASK[0] = 0x00
SHIFT_MASK[1] = 0x80
SHIFT_MASK[2] = 0xC0
SHIFT_MASK[3] = 0xE0
SHIFT_MASK[4] = 0xF0
SHIFT_MASK[5] = 0xF8
SHIFT_MASK[6] = 0xFC
SHIFT_MASK[7] = 0xFE

# TPERM hash table (256 values)
cdef int TPERM[256]

# CTW math tables - using Python list indexing for simplicity
cdef object CTWlogar_list
cdef object CTWzlogpmax_list
cdef object CTWzlogpmin_list
cdef object CTWjacar_list
cdef int JACENTRIES = 1128  # Actual size from CTWJACAR
cdef int LOGENTRIES = 16384
cdef int MAXCOUNTS = 512
cdef int ACCURACY = 128


def init_tperm():
    """Initialize TPERM hash table from Python list."""
    cdef int i
    from zctw._tables import TPERM_TABLE
    for i in range(256):
        TPERM[i] = TPERM_TABLE[i]


def init_math_tables():
    """Initialize Cython views of CTW math tables."""
    global CTWlogar_list, CTWzlogpmax_list, CTWzlogpmin_list, CTWjacar_list
    
    from zctw._tables import CTWLOGAR, CTWZLOGPMAX, CTWZLOGPMIN, CTWJACAR
    
    CTWlogar_list = CTWLOGAR
    CTWzlogpmax_list = CTWZLOGPMAX
    CTWzlogpmin_list = CTWZLOGPMIN
    CTWjacar_list = CTWJACAR


def init_cython():
    """Initialize all Cython tables."""
    init_tperm()
    init_math_tables()
    return True


cdef inline int _hash1(int c, int mask) nogil:
    """Hash function for tree index."""
    return TPERM[c] & mask


cdef inline int _itocptr(int i, int nrtries, int phase) nogil:
    """Convert index, nrtries, phase to symbol pointer."""
    return (((nrtries - 1) << 3) | phase) << 24 | i


cdef inline int _cptrtoi(int p) nogil:
    """Get index from symbol pointer."""
    return p & 0x00FFFFFF


cdef int CTWjac_cython(int ent) except -1:
    """Jacobian logarithm lookup - Python callable version."""
    cdef int idx = -ent
    if idx >= 0 and idx < JACENTRIES:
        return CTWjacar_list[idx]
    return 0


def ctw_jac(ent):
    """Python wrapper for CTWjac."""
    return CTWjac_cython(ent)


def ctw_logar(idx):
    """Python wrapper for CTWlogar."""
    return CTWlogar_list[idx]


def ctw_zlogpmax(idx):
    """Python wrapper for CTWzlogpmax."""
    return CTWzlogpmax_list[idx]


def ctw_zlogpmin(idx):
    """Python wrapper for CTWzlogpmin."""
    return CTWzlogpmin_list[idx]
