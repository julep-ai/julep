FROM python:3.10

# get portaudio and ffmpeg
RUN apt-get update \
        && apt-get install libportaudio2 libportaudiocpp0 portaudio19-dev libasound-dev libsndfile1-dev curl gcc build-essential -y \
        && curl -sSL https://install.python-poetry.org | python3 -

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

WORKDIR /code
COPY ./pyproject.toml /code/pyproject.toml
COPY ./poetry.lock /code/poetry.lock
RUN poetry install
COPY main.py /code/main.py
COPY static /code/static

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]