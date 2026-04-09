# CTW Optimization Findings

## Goal
Optimize Python/Cython CTW (Context Tree Weighting) compression library to close the performance gap with the reference C implementation while maintaining bit-level compatibility.

## Benchmark Results

### Current Performance (50KB data)
| Version    | Encode Time | Decode Time | Speed      |
|------------|-------------|-------------|------------|
| Reference C | ~150ms     | ~160ms      | ~300 KB/s  |
| Cython     | ~2.2s       | ~2.3s       | ~22 KB/s   |
| Pure Python| ~3.1s       | ~3.6s       | ~15 KB/s   |

**Gap: Python is ~18-20x slower than C**

## Root Cause Analysis

### Profiling Results (Pure Python, 50KB)
- `find_path`: 55% of time - 800K calls (8 phases × 50K bytes)
- `ctw_process`: 8%
- `larc.encode/decode`: 7%
- `update_path`: 3%

**Main bottleneck**: ~16 Python function calls per byte processed

The fundamental issue is Python's interpreter overhead per operation, not a specific algorithmic inefficiency.

## Optimizations Applied

### 1. ctwtree.py - find_path optimizations
- Pre-computed `fb_len = len(filebuffer)` once at function start
- Pre-computed `phase_shift = (phase + 1) << 1` instead of recomputing in loops
- Replaced all `len(filebuffer)` calls with cached `fb_len`
- Inlined `_hash1` function directly: `_tperm[ctxstring[depth - 1]] & (maxnrnodes - 1)`
- Added ctwinfo list pool (8 pre-allocated lists) to avoid repeated list allocation

### 2. _compressor.py
- Pre-computed bit positions and treedepth in _encode_byte/_decode_byte
- Cached SHIFT_MASK at module level

### 3. Earlier optimizations
- Removed duplicate SHIFT_MASK tuple creation in functions
- Cached settings attributes in local variables

## Key Insights from Research

### From CTW Papers
1. The C implementation uses macro inlining (`#define hash1(c)`) - no function call overhead
2. PAQ/ZPAQ use hash tables with cache-aware design (1-2 cache misses per lookup)
3. The algorithm is already O(depth) per symbol - main overhead is Python's per-operation cost

### What CAN be optimized (bit-level compatible)
- Minimize attribute lookups ✅ (done - cached in local variables)
- Inline hot functions ✅ (done - inlined _hash1)
- Pre-compute constants ✅ (done - fb_len, phase_shift)
- Reduce list/tuple creation ✅ (done - ctwinfo pool)

### What CANNOT be optimized without breaking compatibility
- Using numpy arrays for tree storage (changes internal representation)
- Changing the tree data structure algorithm
- Using different hash functions

## Bit-Level Compatibility

All optimizations maintain bit-level compatibility:
- Tests pass: round-trip encoding/decoding
- Python produces identical compressed output to C version
- No changes to compression algorithm logic

## Conclusion

The ~18x gap between Python and C is fundamental to Python's interpreter overhead. Each of the ~800K find_path calls for 50KB involves multiple Python-level operations that cannot be optimized further without fundamentally changing the approach (e.g., using Cython with more aggressive typing, or moving to a different algorithm).

The remaining optimization path would be:
1. Aggressive Cython typing (cdef functions, typed memoryviews)
2. Implementing critical paths in C
3. Using numpy for bulk operations where applicable
