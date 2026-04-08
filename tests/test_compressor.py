"""Tests for CTWCompressor encode/decode functionality."""

import pytest

from ctwpy import CTWCompressor, CTWSettings


class TestEncodeEmptyInput:
    """Test encoding empty input."""

    def test_encode_empty_bytes(self, compressor):
        """Empty input should return empty output."""
        result = compressor.encode(b"")
        assert result == b""

    def test_decode_empty_bytes(self, compressor):
        """Decoding empty bytes should return empty output."""
        result = compressor.decode(b"")
        assert result == b""


class TestEncodeSingleByte:
    """Test encoding single byte input."""

    def test_encode_single_byte(self, compressor):
        """Should encode single byte correctly."""
        original = b"\x00"
        compressed = compressor.encode(original)
        decompressed = compressor.decode(compressed)
        assert decompressed == original

    def test_encode_single_byte_value_255(self, compressor):
        """Should encode byte 0xFF correctly."""
        original = b"\xff"
        compressed = compressor.encode(original)
        decompressed = compressor.decode(compressed)
        assert decompressed == original


class TestEncodeInputSmallerThanTreeDepth:
    """Test encoding input smaller than tree depth."""

    def test_encode_3_bytes_treedepth_6(self, compressor):
        """Input smaller than treedepth should encode with probability 0.5."""
        original = b"abc"
        compressed = compressor.encode(original)
        decompressed = compressor.decode(compressed)
        assert decompressed == original


class TestTreeArrayFull:
    """Test behavior when tree array is full."""

    def test_encode_with_small_max_nodes(self, small_compressor):
        """Should work correctly with limited max nodes."""
        original = b"a" * 100
        compressed = small_compressor.encode(original)
        decompressed = small_compressor.decode(compressed)
        assert decompressed == original


class TestInvalidSettings:
    """Test handling of invalid settings."""

    def test_invalid_treedepth_too_high(self):
        """Should raise ValueError for treedepth > 12."""
        settings = CTWSettings(treedepth=20)
        with pytest.raises(ValueError, match="tree depth must be between"):
            CTWCompressor(settings)

    def test_invalid_treedepth_too_low(self):
        """Should raise ValueError for treedepth < 1."""
        settings = CTWSettings(treedepth=0)
        with pytest.raises(ValueError, match="tree depth must be between"):
            CTWCompressor(settings)

    def test_invalid_maxnrnodes_not_power_of_2(self):
        """Should raise ValueError for non-power of 2 maxnrnodes."""
        settings = CTWSettings(maxnrnodes=1000)
        with pytest.raises(ValueError, match="number of nodes must be a power of 2"):
            CTWCompressor(settings)

    def test_invalid_maxnrtries_too_high(self):
        """Should raise ValueError for maxnrtries > 32."""
        settings = CTWSettings(maxnrtries=100)
        with pytest.raises(ValueError, match="number of tries must be between"):
            CTWCompressor(settings)


class TestCorruptedCompressedFile:
    """Test handling of corrupted compressed data."""

    def test_decode_truncated_header(self, compressor):
        """Should raise error for truncated header."""
        with pytest.raises(Exception):
            compressor.decode(b"truncated")

    def test_decode_invalid_magic_bytes(self, compressor):
        """Should raise error for invalid magic bytes."""
        invalid_data = b"NOTCTW" + b"\x00" * 100
        with pytest.raises(Exception):
            compressor.decode(invalid_data)


class TestCompressionCorrectness:
    """Test compression correctness."""

    def test_encode_decode_text(self, compressor):
        """Should correctly encode and decode text."""
        original = b"Hello, World! This is a test of the CTW compression algorithm."
        compressed = compressor.encode(original)
        decompressed = compressor.decode(compressed)
        assert decompressed == original

    def test_encode_decode_repeated_data(self, compressor):
        """Should handle repeated data well."""
        original = b"aaaaaaaabbbbbbbbccccccc" * 10
        compressed = compressor.encode(original)
        decompressed = compressor.decode(compressed)
        assert decompressed == original

    def test_encode_decode_random_data(self, compressor):
        """Should handle random-looking data."""

        original = bytes(range(256))
        compressed = compressor.encode(original)
        decompressed = compressor.decode(compressed)
        assert decompressed == original


class TestCompressionRatio:
    """Test compression ratio characteristics."""

    def test_highly_compressible_data(self, compressor):
        """Should compress highly redundant data significantly."""
        original = b"A" * 1000
        compressed = compressor.encode(original)
        ratio = len(compressed) / len(original)
        assert ratio < 0.5

    def test_incompressible_data(self, compressor):
        """Should not expand incompressible data too much."""
        import os

        original = os.urandom(1000)
        compressed = compressor.encode(original)
        ratio = len(compressed) / len(original)
        assert ratio < 2.0


class TestDifferentSettings:
    """Test with different CTWSettings."""

    def test_custom_treedepth(self):
        """Should work with custom treedepth."""
        settings = CTWSettings(treedepth=8)
        compressor = CTWCompressor(settings)
        original = b"test data"
        compressed = compressor.encode(original)
        decompressed = compressor.decode(compressed)
        assert decompressed == original

    def test_krichevski_trofimov_estimator(self):
        """Should work with KT estimator."""
        settings = CTWSettings(use_zeroredundancy=False)
        compressor = CTWCompressor(settings)
        original = b"test data"
        compressed = compressor.encode(original)
        decompressed = compressor.decode(compressed)
        assert decompressed == original

    def test_root_weighting_enabled(self):
        """Should work with root weighting enabled."""
        settings = CTWSettings(rootweighting=True)
        compressor = CTWCompressor(settings)
        original = b"test data"
        compressed = compressor.encode(original)
        decompressed = compressor.decode(compressed)
        assert decompressed == original

    def test_strict_pruning_disabled(self):
        """Should work with strict pruning disabled."""
        settings = CTWSettings(strictpruning=False)
        compressor = CTWCompressor(settings)
        original = b"test data"
        compressed = compressor.encode(original)
        decompressed = compressor.decode(compressed)
        assert decompressed == original
