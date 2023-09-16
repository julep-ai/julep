FROM python:3.11-slim

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app

WORKDIR $APP_HOME
COPY . ./

RUN poetry install -e .

CMD ["python", "memory_api/web.py", "--host", "0.0.0.0", "--port", "8080"]
