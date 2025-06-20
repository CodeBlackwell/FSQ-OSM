from scripts.feature_engineering import haversine_distance

def test_haversine_zero_distance():
    assert abs(haversine_distance(40.7128, -74.0060, 40.7128, -74.0060)) < 1e-6

def test_haversine_known_distance():
    # New York City (40.7128, -74.0060) to Los Angeles (34.0522, -118.2437)
    dist = haversine_distance(40.7128, -74.0060, 34.0522, -118.2437)
    # Actual is ~3936 km, allow small error
    assert 3900 < dist < 4000

def test_haversine_antipodal():
    # Antipodal points (should be ~20015 km, half Earth's circumference)
    dist = haversine_distance(0, 0, 0, 180)
    assert 20000 < dist < 20040
