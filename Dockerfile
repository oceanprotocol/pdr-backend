##
## Copyright 2024 Ocean Protocol Foundation
## SPDX-License-Identifier: Apache-2.0
##
FROM python:3.11-slim
WORKDIR /app
ADD . /app
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["/app/entrypoint.sh"]
