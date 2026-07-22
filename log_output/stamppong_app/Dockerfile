FROM python:3.12-slim

WORKDIR /app

COPY stamppong.py /app/stamppong.py

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "stamppong.py"]
