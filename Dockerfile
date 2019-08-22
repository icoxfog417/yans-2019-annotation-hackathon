ARG PYTHON_VERSION="3.7"
FROM python:${PYTHON_VERSION}-stretch AS builder

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /yans
WORKDIR /yans

ENTRYPOINT ["python", "yans/hello.py"]
CMD [""]
