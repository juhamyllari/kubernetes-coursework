FROM python:3.12-slim

WORKDIR /app

COPY log_reader.py /app/log_reader.py

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "log_reader.py"]
