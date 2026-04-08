"""Build script for zctw Cython extensions.

This allows pip to build the Cython extension when installing from source.

Usage:
    pip install .                    # Install with pre-built extension if available
    pip install --no-binary :all: .  # Build from source with Cython
"""

import os
import sys
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize

# Get the directory where this setup.py is located
SETUP_DIR = Path(__file__).parent.resolve()

# Change to setup.py directory for relative paths
os.chdir(SETUP_DIR)

# Find .pyx files
src_dir = SETUP_DIR / "src" / "zctw"
pyx_files = list(src_dir.glob("*.pyx"))

if pyx_files:
    ext_modules = []
    for pyx in pyx_files:
        ext_name = f"zctw.{pyx.stem}"
        # Use relative path with forward slashes
        rel_path = str(pyx.relative_to(SETUP_DIR)).replace(os.sep, "/")
        ext_modules.append(
            Extension(
                ext_name,
                sources=[rel_path],
                include_dirs=["src"],
                extra_compile_args=["-O3", "-ffast-math"],
            )
        )

    ext_modules = cythonize(
        ext_modules,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
    )
else:
    ext_modules = []

# Read version from pyproject.toml
try:
    import tomllib

    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)
        version = config["project"]["version"]
except Exception:
    version = "0.1.0"

setup(ext_modules=ext_modules, version=version)
