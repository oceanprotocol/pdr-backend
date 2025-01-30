import os

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.aimodel.xycsv import XycsvMgr


def _getxy_2d():
    X = np.array([[1.1, 1.2], [2.1, 2.2], [3.1, 3.2], [4.1, 4.2]])
    y = np.array([0.1, 0.2, 0.3, 0.4])
    return (X, y)


def _getxy_1d():
    X = np.array([[1.1], [2.1], [3.1], [4.1]])
    y = np.array([0.1, 0.2, 0.3, 0.4])
    return (X, y)


@enforce_types
def test_xycsv_2d(tmp_path):
    # setup
    X, y = _getxy_2d()
    xy_dir = str(tmp_path)
    runid = 12345
    iter_number = 72

    # work
    mgr = XycsvMgr(xy_dir, runid)
    mgr.save_xy(X, y, iter_number)
    X2, y2 = mgr.load_xy(iter_number)

    # test
    assert len(X2.shape) == 2
    assert len(y2.shape) == 1
    assert X2.shape[0] == y2.shape[0]

    np.testing.assert_array_equal(X, X2)
    np.testing.assert_array_equal(y, y2)


@enforce_types
def test_xycsv_1d(tmp_path):
    # setup
    X, y = _getxy_1d()
    xy_dir = str(tmp_path)
    runid = 12345
    iter_number = 72

    # work
    mgr = XycsvMgr(xy_dir, runid)
    mgr.save_xy(X, y, iter_number)
    X2, y2 = mgr.load_xy(iter_number)

    # test
    assert len(X2.shape) == 2
    assert len(y2.shape) == 1
    assert X2.shape[0] == y2.shape[0]

    np.testing.assert_array_equal(X, X2)
    np.testing.assert_array_equal(y, y2)


@enforce_types
def test_xycsv_dirs(tmp_path):
    # setup
    X, y = _getxy_2d()
    xy_dir = str(tmp_path)
    runid = 12345
    iter_number = 72
    mgr = XycsvMgr(xy_dir, runid)

    # work
    mgr.save_xy(X, y, iter_number)

    # test
    assert mgr.saved_iters == [iter_number]

    assert os.path.exists(mgr.abs_xy_dir)
    assert os.path.exists(mgr.abs_run_dir)
    xf, yf = mgr.abs_xy_filenames(iter_number)
    assert os.path.exists(xf)
    assert os.path.exists(yf)

    assert xy_dir in xf
    assert str(runid) in xf
    assert str(iter_number) in xf

    assert xf.replace("X", "y") == yf
