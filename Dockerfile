ARG PYTHON_VERSION="3.7"
FROM python:${PYTHON_VERSION}-stretch AS builder

COPY . /yans
WORKDIR /yans

COPY requirements.txt /
RUN pip install -r /requirements.txt

ENTRYPOINT ["python", "yans/data/train.py"]
CMD [""]
