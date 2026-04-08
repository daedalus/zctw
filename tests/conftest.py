"""Pytest configuration and fixtures for zctw tests."""

import pytest

from zctw import CTWCompressor, CTWSettings


@pytest.fixture
def default_settings():
    """Return default CTWSettings for testing."""
    return CTWSettings()


@pytest.fixture
def compressor(default_settings):
    """Return CTWCompressor with default settings."""
    return CTWCompressor(default_settings)


@pytest.fixture
def small_settings():
    """Return CTWSettings with small values for testing."""
    return CTWSettings(
        treedepth=2,
        maxnrnodes=1024,
        maxnrtries=4,
        maxfilebufsize=1024,
        maxlogbeta=256,
    )


@pytest.fixture
def small_compressor(small_settings):
    """Return CTWCompressor with small settings."""
    return CTWCompressor(small_settings)


@pytest.fixture
def custom_settings():
    """Return CTWSettings with custom values."""
    return CTWSettings(
        treedepth=4,
        maxnrnodes=4096,
        maxnrtries=8,
        maxfilebufsize=4096,
        maxlogbeta=512,
    )
