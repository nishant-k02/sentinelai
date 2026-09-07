import sentinelai


def test_package_imports() -> None:
    """The package is installed and importable (src-layout wired correctly)."""
    assert sentinelai.__name__ == "sentinelai"
