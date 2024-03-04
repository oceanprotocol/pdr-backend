from pdr_backend.lake.base_data_store import BaseDataStore


def _get_test_manager(tmpdir):
    return BaseDataStore(str(tmpdir))


def test__generate_view_name(tmpdir):
    """
    Test the _generate_view_name method.
    """
    test_manager = _get_test_manager(tmpdir)
    view_name = test_manager._generate_view_name(str(tmpdir))

    # check if the view name starts with "dataset_"
    assert view_name.startswith(
        "dataset_"
    ), "The view name does not start with 'dataset_'"
    # check if the view name continues with a hash
    assert len(view_name) > 8, "The view name is too short"
