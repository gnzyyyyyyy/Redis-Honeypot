FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY ingest.py .

RUN pip install requests urllib3

CMD ["python3", "-u", "ingest.py"]
