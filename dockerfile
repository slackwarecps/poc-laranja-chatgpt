FROM python:3
COPY . /work
WORKDIR /work

EXPOSE 8080

RUN pip install --no-cache-dir -r requirements.txt

CMD gunicorn --workers 2 --bind 0.0.0.0:8080 app:app