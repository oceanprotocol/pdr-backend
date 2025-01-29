from enforce_typing import enforce_types
import numpy as np

from pdr_backend.aimodel.xycsv import save_xy, load_xy


@enforce_types
def _getxy():
    X = np.array([[1.1, 1.2], [2.1, 2.2], [3.1, 3.2], [4.1, 4.2]])
    y = np.array([0.1, 0.2, 0.3, 0.4])
    return (X, y)


@enforce_types
def test_xycsv_main(tmp_path):
    filepath = str(tmp_path)
    X, y = _getxy()

    X_filename, y_filename = save_xy(X, y, filepath)
    assert filepath in X_filename
    assert filepath in y_filename
    assert "X_" in X_filename and X_filename[-4:] == ".csv"
    assert "y_" in y_filename and y_filename[-4:] == ".csv"

    X2, y2 = load_xy(X_filename, y_filename)
    np.testing.assert_array_equal(X, X2)
    np.testing.assert_array_equal(y, y2)


@enforce_types
def test_xycsv_unique_filenames(tmp_path):
    filepath = str(tmp_path)
    X, y = _getxy()

    X_filenames, y_filenames = [], []

    for _ in range(50):
        X_filename, y_filename = save_xy(X, y, filepath)
        assert X_filename not in X_filenames
        assert y_filename not in y_filenames
        X_filenames.append(X_filename)
        y_filenames.append(y_filename)
