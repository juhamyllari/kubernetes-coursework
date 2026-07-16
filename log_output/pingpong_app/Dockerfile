FROM python:3.12-slim

WORKDIR /app

COPY pingpong.py /app/pingpong.py

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "pingpong.py"]
