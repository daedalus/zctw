"""Build script for Cython extensions."""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "zctw._cython_ctw",
        sources=["src/zctw/_cython_ctw.pyx"],
        include_dirs=["src"],
        language="c",
        extra_compile_args=["-O3", "-ffast-math"],
    ),
]

setup(
    name="zctw",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
    ),
)
