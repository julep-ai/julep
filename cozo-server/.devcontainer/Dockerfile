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

###############
## WORKSPACE ##
###############

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY ./workspace/requirements.txt $APP_HOME/

RUN pip install -r requirements.txt

COPY ./workspace $APP_HOME/

CMD [ \
    "jupyter", "lab", \
    "--ip", "0.0.0.0", "--port", "8888", \
    "--allow-root", "--no-browser", "--NotebookApp.token=''", "--NotebookApp.password=''" \
]
