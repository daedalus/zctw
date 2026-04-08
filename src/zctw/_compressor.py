"""Main CTW compressor module."""

import io

from zctw.ctwproc import CTWProb, ctw_process, ctw_steps, ctw_data_from_one_count
from zctw.ctwtree import CTWTree, byte_bit, byte_prefix
from zctw.header import read_header, write_header
from zctw.larc import STEPHALF, ArithmeticDecoder, ArithmeticEncoder
from zctw.settings import CTWSettings, check_settings

MAX_TREEDEPTH = 12

CTW_DATA_ZERO = (0, 0, 0)


class CTWCompressor:
    """Context Tree Weighting compressor."""

    def __init__(self, settings: CTWSettings | None = None):
        """Initialize CTW compressor."""
        self.settings = settings if settings is not None else CTWSettings()
        errors = check_settings(self.settings)
        if errors:
            raise ValueError(f"Invalid settings: {', '.join(errors)}")
        self._tree: CTWTree | None = None
        self._encoder: ArithmeticEncoder | None = None
        self._decoder: ArithmeticDecoder | None = None
        self._ctwinfo: list[tuple[int, int, int]] | None = None
        self._dummy0info: list[tuple[int, int, int]] | None = None
        self._dummy1info: list[tuple[int, int, int]] | None = None
        self._ctxstring: list[int] | None = None
        self._phase = 0
        self._curdepth = 0
        self._nrsymbols = 0
        self._databytes = 0
        self._codebits = 0

    def encode(self, data: bytes) -> bytes:
        """Encode data using CTW."""
        self._databytes = len(data)

        if self._databytes == 0:
            return b""

        self._setup_encoding()

        if self.settings.maxfilebufsize > self._databytes:
            self._tree.filebuffer = bytearray(self._databytes)

        nrsymbols = 0
        for nrsymbols in range(min(self.settings.treedepth + 1, self._databytes)):
            let = data[nrsymbols]
            self._tree.filebuffer[nrsymbols] = let
            for phase in range(8):
                self._encoder.encode(STEPHALF, byte_bit(let, phase))

        if nrsymbols < self._databytes - 1:
            self._tree.init_tree(data[nrsymbols])
            self._tree.init_ctxstring()
            self._ctxstring = self._tree.get_ctxstring()

            for i in range(nrsymbols + 1, self._databytes):
                self._encode_byte(data[i])

        self._codebits = self._encoder.exit()
        compressed = self._encoder.file.getvalue()
        self._cleanup()

        return compressed

    def decode(self, compressed: bytes) -> bytes:
        """Decode CTW compressed data."""
        if len(compressed) == 0:
            return b""

        self._setup_decoding(compressed)

        if self.settings.maxfilebufsize > self._databytes:
            self._tree.filebuffer = bytearray(self._databytes)

        nrsymbols = 0
        output = bytearray(self._databytes)
        for nrsymbols in range(min(self.settings.treedepth + 1, self._databytes)):
            let = 0
            for phase in range(8):
                decoded_small = self._decoder.decode(STEPHALF)
                let = (let << 1) | (1 if decoded_small else 0)
            self._tree.filebuffer[nrsymbols] = let
            output[nrsymbols] = let

        if nrsymbols < self._databytes - 1:
            self._tree.init_tree(output[nrsymbols])
            self._tree.init_ctxstring()
            self._ctxstring = self._tree.get_ctxstring()

            for i in range(nrsymbols + 1, self._databytes):
                output[i] = self._decode_byte()

        self._cleanup()
        return bytes(output)

    def _setup_encoding(self) -> None:
        """Setup for encoding."""
        self._tree = CTWTree(self.settings)
        self._tree.init_filebuffer(self._databytes)

        self._encoder = ArithmeticEncoder()
        self._encoder.file = io.BytesIO()
        self._encoder.init(self._encoder.file)

        write_header(self._encoder.file, self._databytes, self.settings)

        self._init_context_arrays()
        self._nrsymbols = 0

    def _setup_decoding(self, compressed: bytes) -> None:
        """Setup for decoding."""
        self._databytes, read_settings = read_header(io.BytesIO(compressed))
        self.settings = read_settings

        self._tree = CTWTree(self.settings)

        if self.settings.maxfilebufsize > self._databytes:
            self._tree.filebuffer = bytearray(self._databytes)
        else:
            self._tree.init_filebuffer(self._databytes)

        self._decoder = ArithmeticDecoder()
        self._decoder.file = io.BytesIO(compressed[12:])
        self._decoder.init(self._decoder.file)

        self._init_context_arrays()
        self._nrsymbols = 0

    def _init_context_arrays(self) -> None:
        """Initialize context arrays."""
        max_depth = self.settings.treedepth + 1
        self._ctwinfo = [CTW_DATA_ZERO for _ in range(max_depth + 1)]
        self._dummy0info = [CTW_DATA_ZERO for _ in range(max_depth + 1)]
        self._dummy1info = [CTW_DATA_ZERO for _ in range(max_depth + 1)]
        self._ctxstring = [0] * (max_depth + 2)
        self._curdepth_list = [0]

    def _encode_byte(self, u: int) -> None:
        """Encode a single byte."""
        SHIFT_MASK = (0x00, 0x80, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC, 0xFE)
        settings = self.settings
        tree = self._tree
        encoder = self._encoder
        ctxstring = self._ctxstring
        dummy0info = self._dummy0info
        dummy1info = self._dummy1info

        for phase in range(8):
            self._phase = phase
            ctxstring[0] = u & SHIFT_MASK[phase]
            bit = (u >> (7 - phase)) & 1

            ctwinfo = tree.find_path(
                phase, self._nrsymbols, ctxstring, self._curdepth_list
            )
            self._curdepth = self._curdepth_list[0]

            ctwprob = CTWProb()
            ctw_process(
                self._curdepth,
                ctwinfo,
                ctwprob,
                dummy0info,
                dummy1info,
                settings,
            )

            instep, symbsmall = ctw_steps(ctwprob)
            encoder.encode(instep, bit == symbsmall)

            if bit:
                tree.update_path(dummy1info)
            else:
                tree.update_path(dummy0info)

        depth_limit = settings.treedepth
        for depth in range(depth_limit, 0, -1):
            ctxstring[depth + 1] = ctxstring[depth]
        ctxstring[1] = u

        if not tree.tree_frozen():
            tree.filebuffer[self._nrsymbols] = u

        self._nrsymbols += 1

    def _decode_byte(self) -> int:
        """Decode a single byte."""
        SHIFT_MASK = (0x00, 0x80, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC, 0xFE)
        settings = self.settings
        tree = self._tree
        decoder = self._decoder
        ctxstring = self._ctxstring
        dummy0info = self._dummy0info
        dummy1info = self._dummy1info

        u = 0
        for phase in range(8):
            self._phase = phase
            ctxstring[0] = u & SHIFT_MASK[phase]

            ctwinfo = tree.find_path(
                phase, self._nrsymbols, ctxstring, self._curdepth_list
            )
            self._curdepth = self._curdepth_list[0]

            ctwprob = CTWProb()
            ctw_process(
                self._curdepth,
                ctwinfo,
                ctwprob,
                dummy0info,
                dummy1info,
                settings,
            )

            instep, symbsmall = ctw_steps(ctwprob)
            decoded_small = decoder.decode(instep)
            bit = decoded_small == symbsmall

            if bit:
                tree.update_path(dummy1info)
            else:
                tree.update_path(dummy0info)

            if bit:
                u |= 1 << (7 - phase)

        depth_limit = settings.treedepth
        for depth in range(depth_limit, 0, -1):
            ctxstring[depth + 1] = ctxstring[depth]
        ctxstring[1] = u

        if not tree.tree_frozen():
            tree.filebuffer[self._nrsymbols] = u

        self._nrsymbols += 1
        return u

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._tree:
            self._tree.free_memory()
        self._tree = None
        self._encoder = None
        self._decoder = None
        self._ctwinfo = None
        self._dummy0info = None
        self._dummy1info = None
        self._ctxstring = None
