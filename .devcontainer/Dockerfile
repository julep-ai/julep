##########
## BASE ##
##########

FROM nvidia/cuda:12.2.0-devel-ubuntu22.04 

ENV PYTHONUNBUFFERED=1

# SYSTEM
RUN apt-get update --yes --quiet && DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends \
    software-properties-common openssh-client \
    build-essential ca-certificates

# PYTHON 3.10
RUN add-apt-repository --yes ppa:deadsnakes/ppa && apt-get update --yes --quiet
RUN DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3.10-distutils \
    python3.10-lib2to3 \
    python3.10-gdbm \
    python3.10-tk \
    pip \
 && rm -rf /var/lib/apt/lists/*

############
## SERVER ##
############

ENV APP_HOME /app
WORKDIR $APP_HOME
RUN \
    pip install --upgrade poetry && \
    poetry config virtualenvs.create false && \
    poetry config installer.max-workers 10

COPY ./dataset/pyproject.toml $APP_HOME/
COPY ./dataset/poetry.lock $APP_HOME/

RUN \
    poetry install \
    -vvv --with dev --no-interaction --no-ansi

COPY ./dataset $APP_HOME/

CMD [ \
    "jupyter", "lab", \
    "--ip", "0.0.0.0", "--port", "8888", \
    "--allow-root", "--no-browser", "--NotebookApp.token=''", "--NotebookApp.password=''" \
]
