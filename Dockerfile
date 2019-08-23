ARG PYTHON_VERSION="3.7"
FROM python:${PYTHON_VERSION}-stretch AS build
RUN python3 -m venv /venv

COPY requirements.txt /
RUN /venv/bin/pip install -r /requirements.txt

FROM python:${PYTHON_VERSION}-stretch AS app
COPY --from=build /venv /venv

COPY . /yans
WORKDIR /yans

ENTRYPOINT ["/venv/bin/python3", "yans/data/train.py"]
