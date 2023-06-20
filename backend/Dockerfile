FROM python:3.10

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1

# to run poetry directly as soon as it's installed
ENV PATH="$POETRY_HOME/bin:$PATH"

# get portaudio and ffmpeg
RUN apt-get update \
        && apt-get install libportaudio2 libportaudiocpp0 portaudio19-dev libasound-dev libsndfile1-dev curl gcc build-essential -y \
        && curl -sSL https://install.python-poetry.org | python3 -

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/code/.venv/bin:$PATH"

ENV HUGGINGFACE_TOKEN=$HUGGINGFACE_TOKEN

RUN pip install huggingface_hub
RUN python -c "import os; from huggingface_hub.hf_api import HfFolder; HfFolder.save_token(os.environ['HUGGINGFACE_TOKEN'])"

WORKDIR /code
COPY ./pyproject.toml /code/pyproject.toml
COPY ./poetry.lock /code/poetry.lock
RUN poetry install --no-root --no-ansi
COPY main.py /code/main.py
COPY generate.py /code/generate.py
COPY static /code/static

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
