"""ctwpy - CLI entry point."""

import argparse
import os
import sys
import time


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CTW (Context Tree Weighting) compression/decompression utility",
        prog="ctwpy",
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="-",
        help="Input file (- for stdin)",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output file (- for stdout)",
    )
    parser.add_argument("-c", "--stdout", action="store_true", help="Write to stdout")
    parser.add_argument("-d", "--decompress", action="store_true", help="Decompress")
    parser.add_argument("-e", "--compress", action="store_true", help="Compress")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite")
    parser.add_argument("-k", "--keep", action="store_true", help="Keep input file")
    parser.add_argument("-t", "--test", action="store_true", help="Test integrity")
    parser.add_argument("-D", "--depth", type=int, metavar="N", help="Tree depth")
    parser.add_argument("-R", "--tries", type=int, metavar="N", help="Max tries")
    parser.add_argument("-n", "--nodes", type=str, metavar="N", help="Max nodes")
    parser.add_argument("-F", "--filesize", type=str, metavar="N", help="Buffer size")
    parser.add_argument("-b", "--beta", type=int, metavar="N", help="Max log beta")
    parser.add_argument(
        "-s", "--no-strict-pruning", action="store_true", help="No pruning"
    )
    parser.add_argument(
        "-w", "--root-weighting", action="store_true", help="Root weighting"
    )
    parser.add_argument(
        "-z", "--zero-redundancy", action="store_true", help="Zero-redundancy"
    )
    parser.add_argument(
        "-K", "--kt-estimator", action="store_true", help="KT estimator"
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    parser.add_argument(
        "-1", action="store_const", dest="compression_level", const=1, help="fastest"
    )
    parser.add_argument(
        "-2",
        action="store_const",
        dest="compression_level",
        const=2,
    )
    parser.add_argument(
        "-3",
        action="store_const",
        dest="compression_level",
        const=3,
    )
    parser.add_argument(
        "-4",
        action="store_const",
        dest="compression_level",
        const=4,
    )
    parser.add_argument(
        "-5",
        action="store_const",
        dest="compression_level",
        const=5,
        help="default",
    )
    parser.add_argument(
        "-6",
        action="store_const",
        dest="compression_level",
        const=6,
    )
    parser.add_argument(
        "-7",
        action="store_const",
        dest="compression_level",
        const=7,
    )
    parser.add_argument(
        "-8",
        action="store_const",
        dest="compression_level",
        const=8,
    )
    parser.add_argument(
        "-9",
        action="store_const",
        dest="compression_level",
        const=9,
        help="best",
    )
    parser.add_argument(
        "--compression-level",
        type=int,
        metavar="N",
        help="Compression level 1-9",
    )

    args = parser.parse_args()

    if args.test:
        return test_file(args.input_file)

    if args.compress and args.decompress:
        print("Error: cannot use both -e and -d", file=sys.stderr)
        return 1

    input_is_stdin = args.input_file == "-"
    output_to_stdout = args.stdout or args.output_file == "-"

    mode = None
    if args.decompress:
        mode = "d"
    elif args.compress:
        mode = "e"
    elif input_is_stdin:
        mode = "e"
    elif args.input_file and args.input_file.endswith(".ctw"):
        mode = "d"
    else:
        mode = "e"

    from ctwpy import CTWCompressor, CTWSettings
    from ctwpy.settings import compression_level_to_settings

    print(
        "CTW (Context Tree Weighting) compression/decompression utility version 0.1",
        file=sys.stderr,
    )

    if args.compression_level is not None:
        try:
            settings = compression_level_to_settings(args.compression_level)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        settings = CTWSettings()
    if args.depth is not None:
        settings.treedepth = args.depth
    if args.tries is not None:
        settings.maxnrtries = args.tries
    if args.nodes is not None:
        settings.maxnrnodes = _parse_size(args.nodes)
    if args.filesize is not None:
        settings.maxfilebufsize = settings.filebufsize = _parse_size(args.filesize)
    if args.beta is not None:
        settings.maxlogbeta = args.beta
    if args.no_strict_pruning:
        settings.strictpruning = False
    if args.root_weighting:
        settings.rootweighting = True
    if args.kt_estimator:
        settings.use_zeroredundancy = False
    if args.zero_redundancy:
        settings.use_zeroredundancy = True

    input_file = args.input_file

    if input_is_stdin:
        if sys.stdin.isatty():
            parser.print_help()
            return 0
    else:
        if not os.path.exists(input_file):
            print(f"Error: {input_file}: No such file", file=sys.stderr)
            return 1

    output_file = args.output_file
    if not output_file:
        if mode == "e":
            output_file = input_file + ".ctw" if not input_is_stdin else "-"
        else:
            output_file = (
                input_file[:-4] if input_file.endswith(".ctw") else input_file + ".dec"
            )
            if input_is_stdin:
                output_file = "-"

    output_to_stdout = args.stdout or output_file == "-"

    if (
        not output_to_stdout
        and input_file != "-"
        and os.path.abspath(input_file) == os.path.abspath(output_file)
    ):
        print("Error: input and output are the same", file=sys.stderr)
        return 1

    if not output_to_stdout and not args.force and os.path.exists(output_file):
        print(
            f"Error: {output_file} exists. Use -f to force overwrite.", file=sys.stderr
        )
        return 1

    try:
        compressor = CTWCompressor(settings)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    start_time = time.time()

    try:
        if mode == "e":
            if input_is_stdin:
                data = sys.stdin.buffer.read()
            else:
                with open(input_file, "rb") as f:
                    data = f.read()
            databytes = len(data)

            if not args.quiet:
                if input_is_stdin:
                    print(
                        f"\nCompress stdin ({databytes} bytes) to {'stdout' if output_to_stdout else output_file}:",
                        file=sys.stderr,
                    )
                else:
                    print(
                        f"\nCompress {input_file} ({databytes} bytes) to {'stdout' if output_to_stdout else output_file}:",
                        file=sys.stderr,
                    )

            compressed = compressor.encode(data)

            if output_to_stdout:
                sys.stdout.buffer.write(compressed)
            else:
                with open(output_file, "wb") as f:
                    f.write(compressed)

            if not args.quiet:
                elapsed = time.time() - start_time
                print("Done.", file=sys.stderr)
                print(
                    f"#bits={len(compressed) * 8}, time={elapsed:.1f}s", file=sys.stderr
                )

            if not args.keep and not input_is_stdin and not output_to_stdout:
                os.remove(input_file)

        else:
            if not args.quiet:
                if input_is_stdin:
                    print(
                        f"\nDecompress stdin to {'stdout' if output_to_stdout else output_file}:",
                        file=sys.stderr,
                    )
                else:
                    print(
                        f"\nDecompress {input_file} to {'stdout' if output_to_stdout else output_file}:",
                        file=sys.stderr,
                    )

            if input_is_stdin:
                compressed = sys.stdin.buffer.read()
            else:
                with open(input_file, "rb") as f:
                    compressed = f.read()

            decompressed = compressor.decode(compressed)

            if output_to_stdout:
                sys.stdout.buffer.write(decompressed)
            else:
                with open(output_file, "wb") as f:
                    f.write(decompressed)

            if not args.quiet:
                elapsed = time.time() - start_time
                print("Done.", file=sys.stderr)
                print(
                    f"#bits={len(compressed) * 8}, time={elapsed:.1f}s", file=sys.stderr
                )

            if not args.keep and not input_is_stdin and not output_to_stdout:
                os.remove(input_file)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    return 0


def test_file(input_file: str) -> int:
    """Test integrity of compressed file."""
    from ctwpy import CTWCompressor, CTWSettings
    from ctwpy.header import read_header

    if input_file == "-":
        print("Error: cannot test stdin", file=sys.stderr)
        return 1

    if not os.path.exists(input_file):
        print(f"Error: {input_file}: No such file", file=sys.stderr)
        return 1

    try:
        with open(input_file, "rb") as f:
            compressed = f.read()

        filesize, settings = read_header(compressed)
        compressor = CTWCompressor(CTWSettings())
        decompressed = compressor.decode(compressed)

        print(f"{input_file}: OK")

    except Exception as e:
        print(f"{input_file}: FAILED - {e}")
        return 1

    return 0


def _parse_size(s: str) -> int:
    """Parse size string with K/M suffixes."""
    s = s.strip()
    if s[-1].upper() == "M":
        return int(s[:-1]) << 20
    elif s[-1].upper() == "K":
        return int(s[:-1]) << 10
    else:
        return int(s)


if __name__ == "__main__":
    sys.exit(main())
