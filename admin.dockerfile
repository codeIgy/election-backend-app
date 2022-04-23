FROM python:3

RUN mkdir -p /opt/src/admin
WORKDIR /opt/src/admin

COPY application/admin/admin.py ./admin.py
COPY application/admin/adminDecorator.py ./adminDecorator.py
COPY application/admin/configuration.py ./configuration.py
COPY application/admin/models.py ./models.py
COPY application/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/admin"

ENTRYPOINT ["python", "./admin.py"]