FROM python:3.6.9

WORKDIR /app

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT 443

CMD gunicorn --bind :$PORT app:app
