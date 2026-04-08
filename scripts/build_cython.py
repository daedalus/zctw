"""Build script for zctw Cython extensions.

This script compiles the Cython extensions. Run this after installing
if the pre-compiled extension is not available for your Python version:

    python scripts/build_cython.py

Or use:

    pip install --no-binary zctw
"""

import sys
import subprocess
from pathlib import Path


def build_extensions():
    """Build Cython extensions."""
    # Build using pip's build isolation
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-build-isolation", "-e", "."],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Build failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print("Build successful!")


if __name__ == "__main__":
    build_extensions()
