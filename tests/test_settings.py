"""Tests for CTWSettings."""

from zctw.settings import CTWSettings, _is_power_of_2, check_settings


class TestCTWSettingsDefaults:
    """Test default CTWSettings values."""

    def test_default_values(self):
        """Should have correct default values."""
        settings = CTWSettings()
        assert settings.treedepth == 6
        assert settings.maxnrnodes == 4194304
        assert settings.maxnrtries == 32
        assert settings.filebufsize == 4194304
        assert settings.maxfilebufsize == 4194304
        assert settings.strictpruning is True
        assert settings.maxlogbeta == 1024
        assert settings.rootweighting is False
        assert settings.use_zeroredundancy is True


class TestCheckSettings:
    """Test settings validation."""

    def test_valid_settings(self):
        """Should return empty list for valid settings."""
        settings = CTWSettings()
        errors = check_settings(settings)
        assert errors == []

    def test_invalid_treedepth_high(self):
        """Should report error for treedepth > 12."""
        settings = CTWSettings(treedepth=15)
        errors = check_settings(settings)
        assert any("tree depth" in e for e in errors)

    def test_invalid_treedepth_low(self):
        """Should report error for treedepth < 1."""
        settings = CTWSettings(treedepth=0)
        errors = check_settings(settings)
        assert any("tree depth" in e for e in errors)

    def test_invalid_maxnrtries_high(self):
        """Should report error for maxnrtries > 32."""
        settings = CTWSettings(maxnrtries=50)
        errors = check_settings(settings)
        assert any("tries" in e for e in errors)

    def test_invalid_maxnrtries_low(self):
        """Should report error for maxnrtries < 1."""
        settings = CTWSettings(maxnrtries=0)
        errors = check_settings(settings)
        assert any("tries" in e for e in errors)

    def test_invalid_maxnrnodes_not_power_of_2(self):
        """Should report error for non-power of 2 maxnrnodes."""
        settings = CTWSettings(maxnrnodes=2049)
        errors = check_settings(settings)
        assert any("power of 2" in e for e in errors)

    def test_invalid_maxnrnodes_too_low(self):
        """Should report error for maxnrnodes < 1024."""
        settings = CTWSettings(maxnrnodes=512)
        errors = check_settings(settings)
        assert any("nodes" in e for e in errors)

    def test_invalid_filebufsize_not_power_of_2(self):
        """Should report error for non-power of 2 filebufsize."""
        settings = CTWSettings(maxfilebufsize=1000)
        errors = check_settings(settings)
        assert any("power of 2" in e for e in errors)

    def test_invalid_maxlogbeta_not_power_of_2(self):
        """Should report error for non-power of 2 maxlogbeta."""
        settings = CTWSettings(maxlogbeta=500)
        errors = check_settings(settings)
        assert any("power of 2" in e for e in errors)


class TestIsPowerOf2:
    """Test power of 2 helper function."""

    def test_power_of_2_values(self):
        """Should return True for powers of 2."""
        assert _is_power_of_2(1) is True
        assert _is_power_of_2(2) is True
        assert _is_power_of_2(4) is True
        assert _is_power_of_2(1024) is True
        assert _is_power_of_2(4194304) is True

    def test_non_power_of_2_values(self):
        """Should return False for non-powers of 2."""
        assert _is_power_of_2(0) is False
        assert _is_power_of_2(3) is False
        assert _is_power_of_2(5) is False
        assert _is_power_of_2(100) is False
        assert _is_power_of_2(1023) is False
