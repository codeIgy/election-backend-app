FROM python:3

RUN mkdir -p /opt/src/election
WORKDIR /opt/src/election

COPY application/configuration.py ./configuration.py
COPY application/migrate.py ./migrate.py
COPY application/models.py ./models.py
COPY application/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/election"

ENTRYPOINT ["python", "./migrate.py"]