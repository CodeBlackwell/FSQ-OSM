import pytest
from scripts.feature_engineering import extract_trigrams

def test_extract_trigrams_basic():
    assert extract_trigrams("Central Park") == [
        'alp', 'ark', 'cen', 'ent', 'lpa', 'ntr', 'par', 'ral', 'tra'
    ]

def test_extract_trigrams_punctuation():
    assert extract_trigrams("Joe's Pizza!") == [
        'esp', 'izz', 'joe', 'oes', 'piz', 'spi', 'zza'
    ]

def test_extract_trigrams_short():
    assert extract_trigrams("OK") == []
    assert extract_trigrams("") == []

def test_extract_trigrams_spaces():
    assert extract_trigrams("   Central   Park   ") == [
        'alp', 'ark', 'cen', 'ent', 'lpa', 'ntr', 'par', 'ral', 'tra'
    ]
