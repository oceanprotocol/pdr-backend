<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

## Install

Here are instructions to install from source.

In a new console:

```console
# clone the repo and enter into it
git clone https://github.com/oceanprotocol/pdr-backend
cd pdr-backend

# Create & activate virtualenv
python -m venv venv
source venv/bin/activate

# Install modules in the environment
pip install -r requirements.txt
```

If you're running MacOS, then also do in the same console:
```console
codesign --force --deep --sign - venv/sapphirepy_bin/sapphirewrapper-arm64.dylib
```
