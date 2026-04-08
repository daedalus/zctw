#!/usr/bin/env python3
"""Comprehensive benchmark for CTW compression.

Compares:
1. Reference C - Original C implementation (ctw binary)
2. Cython - Cython-compiled version (uses .so files)
3. Pure Python - Pure Python implementation (no compiled extensions)

Usage:
    python benchmark_all.py
"""

import sys
import time
import os
import shutil
import statistics
import random
import subprocess

TEST_SIZES = [1000, 5000, 10000, 50000]
ITERATIONS = 3
WARMUP = 1
REF_CTW = "/home/dclavijo/my_code/daedalus-repos/ctw_ref/ctw"


def generate_test_data(size: int, seed: int = 42) -> bytes:
    """Generate test data: mix of repetitive and random bytes."""
    random.seed(seed)
    data = bytearray()
    for _ in range(size):
        if random.random() < 0.7:
            data.append(random.randint(0, 3))
        else:
            data.append(random.randint(0, 255))
    return bytes(data)


def format_time(t: float) -> str:
    """Format time in appropriate unit."""
    if t < 0.001:
        return f"{t * 1e6:>7.1f}µs"
    elif t < 1:
        return f"{t * 1e3:>7.1f}ms"
    else:
        return f"{t:>7.2f}s"


def format_throughput(size: int, time_val: float) -> str:
    """Format throughput in appropriate unit."""
    if time_val == 0:
        return "N/A"
    mbps = size / time_val / 1e6
    kbps = size / time_val / 1e3
    if mbps >= 1:
        return f"{mbps:.2f} MB/s"
    else:
        return f"{kbps:.1f} KB/s"


def benchmark_ref_c(data: bytes, temp_dir: str) -> dict:
    """Benchmark reference C implementation."""
    input_file = os.path.join(temp_dir, "input.bin")
    output_file = os.path.join(temp_dir, "output.ctw")

    with open(input_file, "wb") as f:
        f.write(data)

    compressed_file = input_file + ".ctw"

    encode_times = []
    for _ in range(ITERATIONS):
        if os.path.exists(compressed_file):
            os.remove(compressed_file)
        start = time.perf_counter()
        result = subprocess.run(
            [REF_CTW, "e", "-y", "-d6", input_file], capture_output=True, cwd=temp_dir
        )
        encode_times.append(time.perf_counter() - start)
    encode_time = statistics.mean(encode_times)
    encode_std = statistics.stdev(encode_times) if len(encode_times) > 1 else 0

    compressed_size = os.path.getsize(compressed_file)

    decoded_file = input_file + ".d"

    decode_times = []
    for _ in range(ITERATIONS):
        if os.path.exists(decoded_file):
            os.remove(decoded_file)
        start = time.perf_counter()
        result = subprocess.run(
            [REF_CTW, "d", "-y", compressed_file], capture_output=True, cwd=temp_dir
        )
        decode_times.append(time.perf_counter() - start)
    decode_time = statistics.mean(decode_times)
    decode_std = statistics.stdev(decode_times) if len(decode_times) > 1 else 0

    with open(decoded_file, "rb") as f:
        decompressed = f.read()

    os.remove(input_file)
    os.remove(compressed_file)
    os.remove(decoded_file)

    if decompressed != data:
        raise ValueError("Ref C: Decompressed data doesn't match original!")

    return {
        "label": "Ref C",
        "size": len(data),
        "encode_time": encode_time,
        "encode_std": encode_std,
        "decode_time": decode_time,
        "decode_std": decode_std,
        "compressed_size": compressed_size,
        "ratio": compressed_size / len(data),
    }


def benchmark_cython(data: bytes) -> dict:
    """Benchmark Cython implementation."""
    from zctw import CTWCompressor

    compressor = CTWCompressor()

    for _ in range(WARMUP):
        compressor.encode(data)

    encode_times = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        compressed = compressor.encode(data)
        encode_times.append(time.perf_counter() - start)

    encode_time = statistics.mean(encode_times)
    encode_std = statistics.stdev(encode_times) if len(encode_times) > 1 else 0

    decode_times = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        decompressed = compressor.decode(compressed)
        decode_times.append(time.perf_counter() - start)

    decode_time = statistics.mean(decode_times)
    decode_std = statistics.stdev(decode_times) if len(decode_times) > 1 else 0

    if decompressed != data:
        raise ValueError("Cython: Decompressed data doesn't match original!")

    return {
        "label": "Cython",
        "size": len(data),
        "encode_time": encode_time,
        "encode_std": encode_std,
        "decode_time": decode_time,
        "decode_std": decode_std,
        "compressed_size": len(compressed),
        "ratio": len(compressed) / len(data),
    }


def benchmark_pure_python(data: bytes, src_dir: str, backup_dir: str) -> dict:
    """Benchmark pure Python implementation."""
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            shutil.copy2(os.path.join(backup_dir, f), os.path.join(src_dir, f))
        shutil.rmtree(backup_dir)

    os.makedirs(backup_dir, exist_ok=True)
    for f in os.listdir(src_dir):
        if f.endswith(".so"):
            shutil.move(os.path.join(src_dir, f), os.path.join(backup_dir, f))

    mods_to_remove = [k for k in sys.modules.keys() if k.startswith("zctw")]
    for mod in mods_to_remove:
        del sys.modules[mod]

    from zctw import CTWCompressor

    compressor = CTWCompressor()

    for _ in range(WARMUP):
        compressor.encode(data)

    encode_times = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        compressed = compressor.encode(data)
        encode_times.append(time.perf_counter() - start)

    encode_time = statistics.mean(encode_times)
    encode_std = statistics.stdev(encode_times) if len(encode_times) > 1 else 0

    decode_times = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        decompressed = compressor.decode(compressed)
        decode_times.append(time.perf_counter() - start)

    decode_time = statistics.mean(decode_times)
    decode_std = statistics.stdev(decode_times) if len(decode_times) > 1 else 0

    if decompressed != data:
        raise ValueError("Pure Python: Decompressed data doesn't match original!")

    return {
        "label": "Pure Python",
        "size": len(data),
        "encode_time": encode_time,
        "encode_std": encode_std,
        "decode_time": decode_time,
        "decode_std": decode_std,
        "compressed_size": len(compressed),
        "ratio": len(compressed) / len(data),
    }


def restore_cython(src_dir: str, backup_dir: str):
    """Restore Cython extensions."""
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            shutil.move(os.path.join(backup_dir, f), os.path.join(src_dir, f))
        shutil.rmtree(backup_dir)

    mods_to_remove = [k for k in sys.modules.keys() if k.startswith("zctw")]
    for mod in mods_to_remove:
        del sys.modules[mod]

    import importlib
    import zctw

    importlib.reload(zctw)


def main():
    print("=" * 100)
    print("CTW Compression - Comprehensive Benchmark: C vs Cython vs Python")
    print("=" * 100)
    print(f"Test data: Mixed 70% repetitive + 30% random")
    print(f"Iterations: {ITERATIONS}, Warmup: {WARMUP}")
    print()

    data_sets = {size: generate_test_data(size) for size in TEST_SIZES}

    src_dir = os.path.join(
        os.path.dirname(__file__) if __file__ else ".", "src", "zctw"
    )
    if not os.path.exists(src_dir):
        src_dir = os.path.join(os.getcwd(), "src", "zctw")
    backup_dir = src_dir + "_backup"

    temp_dir = "/tmp/ctw_bench"
    os.makedirs(temp_dir, exist_ok=True)

    results = []

    print("=" * 80)
    print("1. REFERENCE C (native binary)")
    print("=" * 80)
    print(f"{'Size':>8} | {'Encode':^18} | {'Decode':^18} | {'Ratio':>6}")
    print("-" * 80)

    for size in TEST_SIZES:
        data = data_sets[size]
        result = benchmark_ref_c(data, temp_dir)
        results.append(("Ref C", size, result))
        print(
            f"{result['size']:>8} | "
            f"{format_time(result['encode_time'])} ±{format_time(result['encode_std'])} | "
            f"{format_time(result['decode_time'])} ±{format_time(result['decode_std'])} | "
            f"{result['ratio']:>5.2f}"
        )

    print()
    print("=" * 80)
    print("2. CYTHON (compiled with Cython)")
    print("=" * 80)
    print(f"{'Size':>8} | {'Encode':^18} | {'Decode':^18} | {'Ratio':>6}")
    print("-" * 80)

    restore_cython(src_dir, backup_dir)

    for size in TEST_SIZES:
        data = data_sets[size]
        result = benchmark_cython(data)
        results.append(("Cython", size, result))
        print(
            f"{result['size']:>8} | "
            f"{format_time(result['encode_time'])} ±{format_time(result['encode_std'])} | "
            f"{format_time(result['decode_time'])} ±{format_time(result['decode_std'])} | "
            f"{result['ratio']:>5.2f}"
        )

    print()
    print("=" * 80)
    print("3. PURE PYTHON (no compiled extensions)")
    print("=" * 80)
    print(f"{'Size':>8} | {'Encode':^18} | {'Decode':^18} | {'Ratio':>6}")
    print("-" * 80)

    for size in TEST_SIZES:
        data = data_sets[size]
        result = benchmark_pure_python(data, src_dir, backup_dir)
        results.append(("Pure Python", size, result))
        print(
            f"{result['size']:>8} | "
            f"{format_time(result['encode_time'])} ±{format_time(result['encode_std'])} | "
            f"{format_time(result['decode_time'])} ±{format_time(result['decode_std'])} | "
            f"{result['ratio']:>5.2f}"
        )

    restore_cython(src_dir, backup_dir)

    print()
    print("=" * 100)
    print("SPEEDUP COMPARISON (relative to Reference C)")
    print("=" * 100)
    print(
        f"{'Size':>8} | {'Cython Encode':>14} | {'Cython Decode':>14} | {'Py Encode':>14} | {'Py Decode':>14}"
    )
    print("-" * 80)

    for size in TEST_SIZES:
        ref_result = next(r[2] for r in results if r[0] == "Ref C" and r[1] == size)
        cython_result = next(r[2] for r in results if r[0] == "Cython" and r[1] == size)
        py_result = next(
            r[2] for r in results if r[0] == "Pure Python" and r[1] == size
        )

        cython_encode = ref_result["encode_time"] / cython_result["encode_time"]
        cython_decode = ref_result["decode_time"] / cython_result["decode_time"]
        py_encode = ref_result["encode_time"] / py_result["encode_time"]
        py_decode = ref_result["decode_time"] / py_result["decode_time"]

        print(
            f"{size:>8} | {cython_encode:>12.2f}x | {cython_decode:>12.2f}x | "
            f"{py_encode:>12.2f}x | {py_decode:>12.2f}x"
        )

    print()
    print("=" * 100)
    print("SUMMARY (50KB data)")
    print("=" * 100)

    size = 50000
    ref_result = next(r[2] for r in results if r[0] == "Ref C" and r[1] == size)
    cython_result = next(r[2] for r in results if r[0] == "Cython" and r[1] == size)
    py_result = next(r[2] for r in results if r[0] == "Pure Python" and r[1] == size)

    print(f"Data size: {size:,} bytes")
    print(
        f"Compressed: {ref_result['compressed_size']:,} bytes ({ref_result['ratio']:.2f}x)"
    )
    print()
    print(
        f"{'Version':<12} | {'Encode Time':>12} | {'Decode Time':>12} | {'Encode Speed':>12} | {'Decode Speed':>12}"
    )
    print(f"{'':<12} | {'':*>12} | {'':*>12} | {'':*>12} | {'':*>12}")

    for label, result in [
        ("Ref C", ref_result),
        ("Cython", cython_result),
        ("Pure Python", py_result),
    ]:
        print(
            f"{label:<12} | {format_time(result['encode_time']):>12} | {format_time(result['decode_time']):>12} | "
            f"{format_throughput(size, result['encode_time']):>12} | {format_throughput(size, result['decode_time']):>12}"
        )

    print()
    print("Speedup relative to Ref C:")
    for label, result in [("Cython", cython_result), ("Pure Python", py_result)]:
        encode_speedup = ref_result["encode_time"] / result["encode_time"]
        decode_speedup = ref_result["decode_time"] / result["decode_time"]
        print(f"  {label}: {encode_speedup:.2f}x encode, {decode_speedup:.2f}x decode")


if __name__ == "__main__":
    main()
