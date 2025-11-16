"""Test to verify pytest is working."""


def test_setup():
    """Verify basic setup is working."""
    assert True


def test_imports():
    """Test that core libraries can be imported."""
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier

    assert np.__version__
    assert pd.__version__
    assert RandomForestClassifier is not None
