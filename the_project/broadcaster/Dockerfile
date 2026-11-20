FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY broadcaster.py /app/broadcaster.py

CMD ["python", "broadcaster.py"]
