FROM python:3

RUN mkdir -p /opt/src/voter
WORKDIR /opt/src/voter

COPY application/voter/configuration.py ./configuration.py
COPY application/voter/voter.py ./voter.py
COPY application/voter/models.py ./models.py
COPY application/voter/roleDecorator.py ./roleDecorator.py
COPY application/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="opt/src/voter"

ENTRYPOINT ["python", "./voter.py"]