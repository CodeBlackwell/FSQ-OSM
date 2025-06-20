import sys
import subprocess
import pytest
import pandas as pd

def test_fetch_osm_integration(tmp_path):
    """
    Integration test: run the script end-to-end against the real Overpass API.
    Verifies that data is pulled live (no stubbing).
    """
    # Correct lon,lat order for Manhattan (min_lon,min_lat,max_lon,max_lat)
    bbox = "-74.020325,40.700292,-73.907000,40.877483"
    output_file = tmp_path / "osm_test.parquet"

    cmd = [
        sys.executable,
        "scripts/fetch_osm.py",
        f"--bbox={bbox}",
        "--output", str(output_file)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"Script exited with {result.returncode}\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )

    assert output_file.exists(), (
        f"Output file {output_file} was not created.\n"
        f"STDERR: {result.stderr}"
    )

    # Read Parquet and verify live data presence
    df = pd.read_parquet(output_file)
    assert not df.empty, "Expected non-empty DataFrame from live Overpass API."

    # Check for amenity column and at least one non-null amenity
    assert "amenity" in df.columns, "Missing 'amenity' column"
    assert df["amenity"].notnull().any(), "No amenity values found in DataFrame"
