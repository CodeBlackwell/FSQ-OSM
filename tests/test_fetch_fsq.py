import os
import subprocess
import pytest
import pandas as pd

def test_fetch_fsq_runs_and_outputs(tmp_path):
    output_file = tmp_path / "fsq_test.parquet"
    bbox = "40.700292,-74.020325,40.877483,-73.907000"  # Manhattan
    cmd = [
        "python", "scripts/fetch_fsq.py",
        "--bbox", bbox,
        "--output", str(output_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert output_file.exists(), f"Output file {output_file} was not created.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    try:
        df = pd.read_parquet(output_file)
    except Exception as e:
        pytest.fail(f"Could not read output parquet: {e}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    # Fail if empty
    assert not df.empty, f"Foursquare fetch returned 0 POIs. Check API credentials, quota, or bounding box.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    print(f"Fetched {len(df)} rows from Foursquare API.")
