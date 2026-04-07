"""ctwpy - CLI entry point."""

import argparse
import os
import sys
import time


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CTW (Context Tree Weighting) compression/decompression utility"
    )
    parser.add_argument(
        "mode", choices=["e", "d", "i"], help="e=encode, d=decode, i=show file info"
    )
    parser.add_argument("input_file", help="Input file")
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output file (default: input_file.ctw for encode, input_file.d for decode)",
    )
    parser.add_argument(
        "-d", "--depth", type=int, metavar="X", help="Set maximum tree depth (1-12)"
    )
    parser.add_argument(
        "-t",
        "--tries",
        type=int,
        metavar="X",
        help="Set maximum number of tries in tree array (1-32)",
    )
    parser.add_argument(
        "-n",
        "--nodes",
        type=str,
        metavar="X",
        help="Set maximum number of nodes (supports K/M suffix, e.g., 4M)",
    )
    parser.add_argument(
        "-f",
        "--filesize",
        type=str,
        metavar="X",
        help="Set maximum file buffer size (supports K/M suffix)",
    )
    parser.add_argument(
        "-b", "--beta", type=int, metavar="X", help="Set maximum value of log beta"
    )
    parser.add_argument(
        "-s",
        "--no-strict-pruning",
        action="store_true",
        help="Disable strict tree pruning",
    )
    parser.add_argument(
        "-r",
        "--root-weighting",
        action="store_true",
        help="Enable weighting at root nodes",
    )
    parser.add_argument(
        "-k",
        "--kt-estimator",
        action="store_true",
        help="Use Krichevski-Trofimov estimator instead of Zero-Redundancy",
    )
    parser.add_argument(
        "-y", "--force", action="store_true", help="Force overwriting of existing files"
    )
    parser.add_argument(
        "-l", "--log", type=str, metavar="FILE", help="Enable logging to file"
    )

    args = parser.parse_args()

    print("CTW (Context Tree Weighting) compression/decompression utility version 0.1")

    # Import here to avoid import overhead for help
    from ctwpy import CTWCompressor, CTWSettings

    # Build settings
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

    input_file = args.input_file
    output_file = args.output_file

    # Default output filenames
    if not output_file:
        if args.mode == "e":
            output_file = input_file + ".ctw"
        elif args.mode == "d":
            if input_file.endswith(".ctw"):
                output_file = input_file[:-4] + ".d"
            else:
                output_file = input_file + ".d"

    # Check for same file
    if input_file == output_file:
        print("Error: input and output file are the same")
        return 1

    # Check for existing output file
    if os.path.exists(output_file) and not args.force:
        response = input(
            f'"{output_file}" already exists and will be replaced. Are you sure (y/n)? '
        )
        if response.lower() != "y":
            return 1

    # Get file size
    databytes = os.path.getsize(input_file)

    # Run encode/decode
    compressor = CTWCompressor(settings)

    start_time = time.time()

    if args.mode == "i":
        # Show file info
        with open(input_file, "rb") as f:
            compressed_data = f.read()

        from ctwpy.header import read_header

        filesize, read_settings = read_header(compressed_data[:100])  # Just need header
        # Re-read to get proper size
        import io

        filesize, read_settings = read_header(io.BytesIO(compressed_data))

        print(f"\nFile: {input_file}")
        print(f"Compressed filesize: {len(compressed_data)} bytes")
        print(f"Uncompressed filesize: {filesize} bytes")
        print("\nCTW settings used for encoding:")
        from ctwpy.settings import print_settings

        print(print_settings(read_settings))

        return 0

    try:
        if args.mode == "e":
            # Encode
            print("\nCurrent CTW settings:")
            from ctwpy.settings import print_settings

            print(print_settings(settings))
            print(f"\nEncode {input_file} ({databytes} bytes) to {output_file}:")
            print("Initializing...")

            with open(input_file, "rb") as f:
                data = f.read()

            compressed = compressor.encode(data)

            with open(output_file, "wb") as f:
                f.write(compressed)

            elapsed = time.time() - start_time
            print("Finished.")
            print("\nStatistics:")
            print(f"#codebits        = {len(compressed) * 8}")
            print(
                f"#treenodes       = {compressor._tree.nrnodes if compressor._tree else 0}"
            )
            print(f"processing time  = {elapsed:.1f} seconds")
            print(f"compression-rate = {len(compressed) * 8 / databytes:.5f} bits/byte")

        elif args.mode == "d":
            # Decode
            print("\nCurrent CTW settings:")
            from ctwpy.settings import print_settings

            print(print_settings(settings))
            print(f"\nDecode {input_file} to {output_file}:")
            print("Initializing...")

            with open(input_file, "rb") as f:
                compressed = f.read()

            decompressed = compressor.decode(compressed)

            with open(output_file, "wb") as f:
                f.write(decompressed)

            elapsed = time.time() - start_time
            print("Finished.")
            print("\nStatistics:")
            print(f"#codebits        = {len(compressed) * 8}")
            print(
                f"#treenodes       = {compressor._tree.nrnodes if compressor._tree else 0}"
            )
            print(f"processing time  = {elapsed:.1f} seconds")
            print(
                f"decompression-rate = {databytes / (len(compressed) * 8):.5f} bytes/bit"
            )

    except Exception as e:
        print(f"Error: {e}")
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
