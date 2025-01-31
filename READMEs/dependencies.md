# Dependency Management

This is a document for devs to understand how dependencies are managed in the `pdr-backend` project.
It also serves users who want to understand any issues and caveats in the installation process.

## Frozen Dependencies

- `pytest-asyncio` is frozen at version 0.21.1. This is because later versions have a known issue with event loops.

For more details, see the [the pytest-asyncio changelog](https://pytest-asyncio.readthedocs.io/en/latest/reference/changelog.html#id1), under Known Issues.
The library itself recommends using version 0.21 until the issue is resolved.

## For new dependencies: Types Management

For type checking, we use mypy, which may require dependencies for type hints.
This means that installing a new package would require installing additional packages for type hints.

In order to avoid conflicts with the main dependencies, we prefer not to install these additional packages.
Consequently, we ignore the missing library stubs in the `mypy.ini` file.

E.g. for pytz types if you see an error like:

```console
error: Library stubs not installed for "pytz"  [import-untyped]
note: Hint: "python3 -m pip install types-pytz"
note: (or run "mypy --install-types" to install all missing stub packages)
note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
```

do NOT install the types-pytz package. Instead, add `pytz` to the `mypy.ini` file under the `[mypy]` section:

```ini
[mypy-pytz.*]
ignore_missing_imports = True
```

Use this approach for any other missing types, naming the section `[mypy-<package_name>].*`.

## For new dependencies/upgrade/removal: Check for warnings

When installing a new package, upgrading, or removing a package, check for warnings.
Currently the CIs fail if there are any warnings in the tests. This is to ensure that the codebase is clean and maintainable.

However, we do supress some errors in `pytest.ini`.

### "Permanent" suppressions: no need to check
- `ignore::pytest.PytestUnhandledThreadExceptionWarning`
- `ignore::pytest.PytestUnraisableExceptionWarning`
- `ignore:.*This process \(pid=.*\) is multi-threaded, use of fork\(\) may lead to deadlocks in the child.*:DeprecationWarning`

These are due to the nature of the pytest tests and are not expected to be resolved.

### "Temporary" suppressions: check and remove

#### Warnings related to plotly
- `ignore:.*setDaemon\(\) is deprecated, set the daemon attribute instead.*:DeprecationWarning` -> due to usage of `kaleido` and `plotly`

If you upgrade plotly, you should check if these warnings are still present and remove the ignore statement in `pytest.ini` if they are not.

#### Warnings related to stopit
- `ignore:.*pkg_resources is deprecated as an API.*:DeprecationWarning` -> due to usage of `stopit`, which is an older library and relies on older versions of `pkg_resources`.

Stopit is a simple wrapper to stop function execution if it takes too long. It is only used in the Sim Plots Dashboard and we should look into removing it.
If you remove the stopit dependency, you should check if these warnings are still present and remove the ignore statement in `pytest.ini` if they are not.

## Updating this document

If dependency upgrades fix some issues, or if policies change and this document needs to be updated, please do so.
Happy coding :)
