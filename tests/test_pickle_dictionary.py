import os
import tempfile

from PickleDictionary import PickleDictionary

TEST_FILES = []


def setup_module(module):
    # Ensure pickles directory exists
    os.makedirs("pickles", exist_ok=True)


def teardown_module(module):
    # Clean up temporary test pickle files
    for test_file in TEST_FILES:
        file_path = f"pickles/{test_file}"
        if os.path.exists(file_path):
            os.remove(file_path)


def _get_temp_filename():
    """Generate a unique temporary filename for test pickles"""
    fd, temp_path = tempfile.mkstemp(suffix=".dat", dir="pickles", prefix="test_")
    os.close(fd)
    os.remove(temp_path)  # Remove the file, just use the name
    filename = os.path.basename(temp_path)
    TEST_FILES.append(filename)
    return filename


def test_creates_file_and_directory():
    filename = _get_temp_filename()
    p = PickleDictionary(filename)
    assert os.path.exists(f"pickles/{filename}")
    # Empty dict initially
    try:
        _ = p["missing"]
        assert False, "Expected KeyError for missing key"
    except KeyError:
        pass


def test_setitem_and_save_persistence():
    filename = _get_temp_filename()
    p = PickleDictionary(filename)
    p["a"] = 1
    p.save()

    # Reload and ensure value is persisted
    p2 = PickleDictionary(filename)
    assert p2["a"] == 1


def test_contains_and_getitem():
    filename = _get_temp_filename()
    p = PickleDictionary(filename)
    p["x"] = "y"
    assert "x" in p
    assert p["x"] == "y"
