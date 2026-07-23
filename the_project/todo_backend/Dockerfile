FROM python:3.12-slim

WORKDIR /app

COPY todo_backend.py /app/todo_backend.py

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "todo_backend.py"]
