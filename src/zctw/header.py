"""CTW file header read/write module."""

from zctw.settings import CTWSettings

HEADERSIZE = 12
CTWFILE_VERSION = 0

F_STRICTPRUNING = 32
F_ROOTWEIGHTING = 64
F_ZEROREDUNDANCY = 128


def _calc_log2(b: int) -> int:
    """Calculate base-2 logarithm of b.
    Returns the correct answer only if b is a power of 2."""
    cnt = 0
    while (b & 1) == 0:
        cnt += 1
        b >>= 1
    return cnt


def _put_bytes(outfile, value: int, cnt: int) -> None:
    """Write cnt bytes in big-endian order (matching C implementation)."""
    for i in range(cnt - 1, -1, -1):
        outfile.write(bytes([(value >> (i * 8)) & 0xFF]))


def _get_bytes(infile, cnt: int) -> int:
    """Read cnt bytes in big-endian order (matching C implementation)."""
    value = 0
    for i in range(cnt):
        value = (value << 8) | infile.read(1)[0]
    return value


def write_header(outfile, filesize: int, settings: CTWSettings) -> None:
    """Write CTW file header."""
    tmp = 0

    _put_bytes(outfile, HEADERSIZE, 2)
    outfile.write(bytes([CTWFILE_VERSION]))
    outfile.write(bytes([0]))
    _put_bytes(outfile, filesize, 4)
    outfile.write(bytes([settings.treedepth]))
    outfile.write(bytes([settings.maxnrtries]))

    tmp = _calc_log2(settings.maxnrnodes)
    if settings.strictpruning:
        tmp |= F_STRICTPRUNING
    if settings.rootweighting:
        tmp |= F_ROOTWEIGHTING
    if settings.use_zeroredundancy:
        tmp |= F_ZEROREDUNDANCY
    outfile.write(bytes([tmp]))

    tmp = _calc_log2(settings.maxfilebufsize) - 9
    tmp |= _calc_log2(settings.maxlogbeta) << 4
    outfile.write(bytes([tmp]))


def read_header(infile) -> tuple[int, CTWSettings]:
    """Read CTW file header."""
    headersize = _get_bytes(infile, 2)
    version = infile.read(1)[0]
    if version != CTWFILE_VERSION:
        raise ValueError("Invalid CTW file version number")

    if headersize < HEADERSIZE:
        raise ValueError("Invalid header size")

    infile.read(1)
    filesize = _get_bytes(infile, 4)

    settings = CTWSettings()
    settings.treedepth = infile.read(1)[0]
    settings.maxnrtries = infile.read(1)[0]

    tmp = infile.read(1)[0]
    settings.maxnrnodes = 1 << (tmp & 31)
    settings.strictpruning = (tmp & F_STRICTPRUNING) != 0
    settings.rootweighting = (tmp & F_ROOTWEIGHTING) != 0
    settings.use_zeroredundancy = (tmp & F_ZEROREDUNDANCY) != 0

    tmp = infile.read(1)[0]
    settings.maxfilebufsize = 1 << ((tmp & 15) + 9)
    if settings.maxfilebufsize > filesize:
        settings.filebufsize = filesize
    else:
        settings.filebufsize = settings.maxfilebufsize
    settings.maxlogbeta = 1 << (tmp >> 4)

    if headersize > HEADERSIZE:
        infile.seek(headersize - HEADERSIZE, 1)

    return filesize, settings
