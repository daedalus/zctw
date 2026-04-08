"""Settings module - contains all CTW algorithm settings and defaults."""

from dataclasses import dataclass

MAX_TREEDEPTH = 12
MIN_TREEDEPTH = 1
MAX_MAXNRNODES = 16777216
MIN_MAXNRNODES = 1024
MAX_MAXNRTRIES = 32
MIN_MAXNRTRIES = 1
MAX_FILEBUFSIZE = 16777216
MIN_FILEBUFSIZE = 512
MAX_MAXLOGBETA = 16384
MIN_MAXLOGBETA = 1


@dataclass
class CTWSettings:
    """Runtime configurable settings for the CTW algorithm."""

    treedepth: int = 6
    maxnrnodes: int = 4194304
    maxnrtries: int = 32
    filebufsize: int = 4194304
    maxfilebufsize: int = 4194304
    strictpruning: bool = True
    maxlogbeta: int = 1024
    rootweighting: bool = False
    use_zeroredundancy: bool = True


def check_settings(settings: CTWSettings) -> list[str]:
    """Validate CTW settings.

    Args:
        settings: CTWSettings instance to validate.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    if not (MIN_TREEDEPTH <= settings.treedepth <= MAX_TREEDEPTH):
        errors.append(f"tree depth must be between {MIN_TREEDEPTH} and {MAX_TREEDEPTH}")

    if not (MIN_MAXNRTRIES <= settings.maxnrtries <= MAX_MAXNRTRIES):
        errors.append(
            f"number of tries must be between {MIN_MAXNRTRIES} and {MAX_MAXNRTRIES}"
        )

    if not _is_power_of_2(settings.maxnrnodes):
        errors.append("number of nodes must be a power of 2")
    elif not (MIN_MAXNRNODES <= settings.maxnrnodes <= MAX_MAXNRNODES):
        errors.append(
            f"number of nodes must be between {MIN_MAXNRNODES} and {MAX_MAXNRNODES}"
        )

    if not (MIN_FILEBUFSIZE <= settings.maxfilebufsize <= MAX_FILEBUFSIZE):
        errors.append(
            f"max file buffer size must be between {MIN_FILEBUFSIZE} and {MAX_FILEBUFSIZE}"
        )
    elif not _is_power_of_2(settings.maxfilebufsize):
        errors.append("max file buffer size must be a power of 2")

    if not (MIN_MAXLOGBETA <= settings.maxlogbeta <= MAX_MAXLOGBETA):
        errors.append(
            f"max log beta must be between {MIN_MAXLOGBETA} and {MAX_MAXLOGBETA}"
        )
    elif not _is_power_of_2(settings.maxlogbeta):
        errors.append("max log beta must be a power of 2")

    return errors


def _is_power_of_2(n: int) -> bool:
    """Check if n is a power of 2."""
    return n > 0 and (n & (n - 1)) == 0


def print_settings(settings: CTWSettings) -> str:
    """Return string representation of settings."""
    return (
        f"Tree depth: {settings.treedepth}\n"
        f"Size of tree array: {settings.maxnrnodes} nodes ({settings.maxnrnodes * 8} bytes)\n"
        f"Max. number of tries in tree array: {settings.maxnrtries}\n"
        f"File buffer size: {settings.filebufsize} bytes (max. {settings.maxfilebufsize})\n"
        f"Strict pruning: {'enabled' if settings.strictpruning else 'disabled'}\n"
        f"Root weighting: {'enabled' if settings.rootweighting else 'disabled'}\n"
        f"Max. log beta: {settings.maxlogbeta}\n"
        f"Estimator: {'Zero-Redundancy' if settings.use_zeroredundancy else 'Krichevski-Trofimov'}"
    )


def compression_level_to_settings(level: int) -> CTWSettings:
    """Create CTWSettings from compression level (1-9).

    Args:
        level: Compression level from 1 (fastest, least compression) to 9 (slowest, best compression)

    Returns:
        CTWSettings configured for the given compression level
    """
    if not 1 <= level <= 9:
        raise ValueError(f"compression level must be between 1 and 9, got {level}")

    settings = CTWSettings()

    if level == 1:
        settings.treedepth = 2
        settings.maxnrnodes = 65536
        settings.maxnrtries = 4
    elif level == 2:
        settings.treedepth = 3
        settings.maxnrnodes = 131072
        settings.maxnrtries = 8
    elif level == 3:
        settings.treedepth = 4
        settings.maxnrnodes = 262144
        settings.maxnrtries = 8
    elif level == 4:
        settings.treedepth = 5
        settings.maxnrnodes = 524288
        settings.maxnrtries = 16
    elif level == 5:
        settings.treedepth = 6
        settings.maxnrnodes = 1048576
        settings.maxnrtries = 16
    elif level == 6:
        settings.treedepth = 8
        settings.maxnrnodes = 2097152
        settings.maxnrtries = 24
    elif level == 7:
        settings.treedepth = 10
        settings.maxnrnodes = 4194304
        settings.maxnrtries = 32
    elif level == 8:
        settings.treedepth = 11
        settings.maxnrnodes = 8388608
        settings.maxnrtries = 32
    else:  # level 9
        settings.treedepth = 11  # Capped at 11 due to ctxstring array bounds
        settings.maxnrnodes = 16777216
        settings.maxnrtries = 32

    settings.filebufsize = settings.maxnrnodes
    settings.maxfilebufsize = settings.maxnrnodes

    return settings
