# Usage for Backend Devs

This is for core devs to improve pdr-backend repo itself.

## Install pdr-backend

Follow directions to install pdr-backend in [predictoor.md](predictoor.md)

### Setup dev environment

Open a new "work" console and:

```console
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set PRIVATE_KEY
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"

```

All other settings are in [`ppss.yaml`](../ppss.yaml). Some of these are used in unit tests. Whereas most READMEs make a copy `my_ppss.yaml`, for development we typically want to operate directly on `ppss.yaml`.

### Local Usage: Testing

In work console, run tests:

```console
# (ensure PRIVATE_KEY set as above)

# run a single test. The "-s" is for more output.
# note that pytest does dynamic type-checking too:)
pytest pdr_backend/util/test_noganache/test_util_constants.py::test_util_constants -s

# run all tests in a file
pytest pdr_backend/util/test_noganache/test_util_constants.py -s

# run all regular tests; see details on pytest markers to select specific suites
pytest
```

### Local Usage: Linting

In work console, run linting checks.

```console
# auto-fix some pylint complaints like whitespace. CI doesn't modify files; we do
black ./

# run linting on code style. Use same setup as CI
pylint --rcfile .pylintrc * pdr_backend/*

# mypy does static type-checking and more. Use same setup as CI
mypy --config-file mypy.ini ./
```

### Local Usage: Run a custom agent

Let's say you want to change the trader agent, and use off-the-shelf agents for everything else. Here's how.

In console:

```console
#(ensure envvars set as above)

# run trader agent, approach 1
pdr trader 1 ppss.yaml development
```

(You can track at finer resolution by writing more logs to the code.)


## Dependencies
See [dependencies.md](dependencies.md) for more details.


