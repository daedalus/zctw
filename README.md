# ctwpy

Python implementation of Context Tree Weighting (CTW) lossless compression.

[![PyPI](https://img.shields.io/pypi/v/ctwpy.svg)](https://pypi.org/project/ctwpy/)
[![Python](https://img.shields.io/pypi/pyversions/ctwpy.svg)](https://pypi.org/project/ctwpy/)
[![Coverage](https://codecov.io/gh/daedalus/ctwpy/branch/main/graph/badge.svg)](https://codecov.io/gh/daedalus/ctwpy)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Install

```bash
pip install ctwpy
```

## Usage

```python
from ctwpy import CTWCompressor, CTWSettings

# Use default settings
compressor = CTWCompressor()

# Or customize settings
settings = CTWSettings(treedepth=8, maxnrnodes=4194304)
compressor = CTWCompressor(settings)

# Compress data
original = b"Hello, World! This is a test of the CTW compression algorithm."
compressed = compressor.encode(original)

# Decompress
decompressed = compressor.decode(compressed)

print(f"Original: {len(original)} bytes")
print(f"Compressed: {len(compressed)} bytes")
print(f"Decompressed matches: {original == decompressed}")
```

## CLI

```bash
# Encode a file
ctwpy e input.txt output.ctw

# Decode a file
ctwpy d output.ctw input_decoded.txt

# Show file info
ctwpy i output.ctw
```

### CLI Options

- `-dX`: Set maximum tree depth (1-12)
- `-tX`: Set maximum number of tries in tree array (1-32)
- `-nX`: Set maximum number of nodes (supports K/M suffix, e.g., 4M)
- `-fX`: Set maximum file buffer size (supports K/M suffix)
- `-bX`: Set maximum value of log beta
- `-s`: Disable strict tree pruning
- `-r`: Enable weighting at root nodes
- `-k`: Use Krichevski-Trofimov estimator instead of Zero-Redundancy
- `-y`: Force overwriting of existing files
- `-lX`: Enable logging to file X

## API

### CTWSettings

```python
@dataclass
class CTWSettings:
    treedepth: int          # max depth of trees, excluding root (default: 6)
    maxnrnodes: int         # max nodes in tree array (default: 4194304)
    maxnrtries: int         # max tries in hash table (default: 32)
    filebufsize: int        # actual file buffer size (default: 4194304)
    maxfilebufsize: int     # max file buffer size (default: 4194304)
    strictpruning: bool     # use strict pruning method (default: True)
    maxlogbeta: int         # max value of logbeta (default: 1024)
    rootweighting: bool     # perform weighting at root node (default: False)
    use_zeroredundancy: bool # use zero-redundancy estimator (default: True)
```

### CTWCompressor

```python
class CTWCompressor:
    def __init__(self, settings: CTWSettings | None = None)
    def encode(self, data: bytes) -> bytes
    def decode(self, compressed: bytes) -> bytes
```

## Development

```bash
git clone https://github.com/daedalus/ctwpy.git
cd ctwpy
pip install -e ".[test]"

# run tests
pytest

# format
ruff format src/ tests/

# lint
ruff check src/ tests/

# type check
mypy src/
```

## License

MIT License - see LICENSE file.