import json
from scripts.feature_engineering import compute_extra_features

def test_string_heuristics_basic():
    row = {"name": "Joe's Pizza LLC"}
    features = json.loads(compute_extra_features(row))
    assert features["name_lower"] == "joe's pizza llc"
    assert features["name_no_punct"] == "joes pizza llc"
    assert features["name_no_punct_space"] == "joespizzallc"
    assert features["name_no_legal_suffix"] == "joes pizza"
    assert features["name_token_count"] == 3
    assert features["name_length"] == len("Joe's Pizza LLC")

def test_string_heuristics_punct_and_space():
    row = {"name": "Central Park, Inc."}
    features = json.loads(compute_extra_features(row))
    assert features["name_lower"] == "central park, inc."
    assert features["name_no_punct"] == "central park inc"
    assert features["name_no_punct_space"] == "centralparkinc"
    assert features["name_no_legal_suffix"] == "central park"
    assert features["name_token_count"] == 3
    assert features["name_length"] == len("Central Park, Inc.")

def test_string_heuristics_empty():
    row = {"name": None}
    features = json.loads(compute_extra_features(row))
    assert features["name_lower"] is None
    assert features["name_no_punct"] is None
    assert features["name_no_punct_space"] is None
    assert features["name_no_legal_suffix"] is None
    assert features["name_token_count"] == 0
    assert features["name_length"] == 0
