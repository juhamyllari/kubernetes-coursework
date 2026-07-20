FROM python:3.12-slim

WORKDIR /app

COPY todo_app.py /app/todo_app.py

COPY requirements.txt /app/requirements.txt

COPY templates /app/templates

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "todo_app.py"]
