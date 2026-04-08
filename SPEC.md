# SPEC.md — zctw

## Purpose

zctw is a Python implementation of the Context Tree Weighting (CTW) lossless compression algorithm. It provides both a Python library for programmatic compression/decompression and a CLI tool for encoding and decoding files.

## Scope

- **In scope:**
  - Full CTW algorithm implementation (encode/decode)
  - Pure Python implementation using only stdlib
  - CLI tool with encode (`e`) and decode (`d`) modes
  - Configurable parameters (tree depth, max nodes, file buffer size, etc.)
  - Support for Zero-Redundancy and Krichevski-Trofimov estimators
  - Arithmetic encoder/decoder implementation
  - File header read/write for compressed files

- **Not in scope:**
  - GUI interface
  - Streaming compression (files must fit in memory)
  - Thread safety / parallel processing

## Public API / Interface

### Library API

```python
from zctw import CTWCompressor

# Initialize compressor with settings
compressor = CTWCompressor(
    treedepth: int = 6,
    maxnrnodes: int = 4194304,
    maxnrtries: int = 32,
    maxfilebufsize: int = 4194304,
    maxlogbeta: int = 1024,
    strictpruning: bool = True,
    rootweighting: bool = False,
    use_zeroredundancy: bool = True,
)

# Encode bytes to compressed bytes
compressed = compressor.encode(data: bytes) -> bytes

# Decode compressed bytes to original bytes
decompressed = compressor.decode(compressed: bytes) -> bytes
```

### CLI Interface

```bash
zctw e <input_file> [<output_file>] [options]
zctw d <input_file> [<output_file>] [options]
```

**Options:**
- `-dX`: Set maximum tree depth (1-12)
- `-tX`: Set maximum number of tries in tree array (1-32)
- `-nX`: Set maximum number of nodes (size of tree array), supports K/M suffix (e.g., 4M)
- `-fX`: Set maximum file buffer size, supports K/M suffix
- `-bX`: Set maximum value of log beta
- `-s`: Disable strict tree pruning
- `-r`: Enable weighting at root nodes
- `-k`: Use Krichevski-Trofimov estimator instead of Zero-Redundancy
- `-y`: Force overwriting of existing files
- `-lX`: Enable logging to file X

**Output file defaults:**
- Encode: `<input_file>.zctw`
- Decode: `<input_file>.d` (removes .zctw extension)

### Data Structures

```python
@dataclass
class CTWSettings:
    treedepth: int          # max depth of trees, excluding root (1-12)
    maxnrnodes: int         # max nodes in tree array (power of 2)
    maxnrtries: int         # max tries in hash table (1-32)
    filebufsize: int        # actual file buffer size (power of 2)
    maxfilebufsize: int     # max file buffer size (power of 2)
    strictpruning: bool     # use strict pruning method
    maxlogbeta: int         # max value of logbeta (power of 2)
    rootweighting: bool     # perform weighting at root node
    use_zeroredundancy: bool # use zero-redundancy estimator
```

## Edge Cases

1. **Empty input**: Handle gracefully (return empty output)
2. **Single byte input**: Encode with initial context
3. **Input smaller than tree depth**: Encode all bytes with probability 0.5
4. **Tree array full**: Freeze tree structure, no new nodes created
5. **Hash collision**: Handle failed node searches up to maxnrtries
6. **File already exists**: Prompt for overwrite or use -y flag
7. **Invalid settings**: Validate and report errors before processing
8. **Corrupted compressed file**: Detect and raise informative error

## Performance & Constraints

- Memory: Tree array requires 8 bytes per node (default 4M nodes = 32MB)
- File buffer requires up to maxfilebufsize bytes
- Time complexity: O(n * treedepth) for encoding/decoding n bytes
- Pure Python implementation (no C extensions)
- All arithmetic uses integer operations for reproducibility