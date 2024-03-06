FROM python:3.8-slim-buster
WORKDIR /app
ADD . /app
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["/app/entrypoint.sh"]
