FROM python:3.10.6-buster

ENV POETRY_VERSION=1.7.1

RUN apt-get update && apt-get install -y \
    python3-requests \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN python3 -m pip install --upgrade pip

RUN pip install poetry==$POETRY_VERSION
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev && rm pyproject.toml

COPY ontologytimemachine /ontologytimemachine

CMD python3 -m proxy --hostname 0.0.0.0 --port $PORT --plugins ontologytimemachine.custom_proxy.OntologyTimeMachinePlugin

