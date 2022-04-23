FROM python:3

RUN mkdir -p /opt/src/daemon
WORKDIR /opt/src/daemon

COPY application/daemon/daemon.py ./daemon.py
COPY application/daemon/configuration.py ./configuration.py
COPY application/daemon/models.py ./models.py
COPY application/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="opt/src/daemon"

ENTRYPOINT ["python", "./daemon.py"]