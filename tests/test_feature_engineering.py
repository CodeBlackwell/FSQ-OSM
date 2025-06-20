import pytest
import pandas as pd
from scripts.feature_engineering import (
    canonicalize_category, fuzzy_category_match, normalize_phone, normalize_website, phone_website_match
)

def test_canonicalize_category():
    assert canonicalize_category('Restaurant', 'fsq') == 'restaurant'
    assert canonicalize_category('coffee shop', 'fsq') == 'cafe'
    assert canonicalize_category('ATM', 'osm') == 'bank'
    assert canonicalize_category('museum', 'osm') == 'museum'
    assert canonicalize_category('randomthing', 'fsq') == 'randomthing'

def test_fuzzy_category_match():
    assert fuzzy_category_match('restaurant', 'restaurant') == 1
    assert fuzzy_category_match('cafe', 'restaurant') == 0
    assert fuzzy_category_match(None, 'restaurant') == 0
    assert fuzzy_category_match('bar', None) == 0

def test_normalize_phone():
    assert normalize_phone('+1 (212) 555-1234') == '12125551234'
    assert normalize_phone('212-555-1234') == '2125551234'
    assert normalize_phone('') is None
    assert normalize_phone(None) is None

def test_normalize_website():
    assert normalize_website('https://www.example.com/') == 'example.com'
    assert normalize_website('http://example.com') == 'example.com'
    assert normalize_website('www.example.com/') == 'example.com'
    assert normalize_website('example.com') == 'example.com'
    assert normalize_website('') is None
    assert normalize_website(None) is None

def test_phone_website_match():
    # Phone matches
    assert phone_website_match('212-555-1234', '2125551234', 'a.com', 'b.com') == 1
    # Website matches
    assert phone_website_match('123', '456', 'https://foo.com', 'foo.com') == 1
    # Neither matches
    assert phone_website_match('123', '456', 'a.com', 'b.com') == 0
    # One side missing
    assert phone_website_match(None, '456', None, 'b.com') == 0
    assert phone_website_match('123', None, 'foo.com', None) == 0
