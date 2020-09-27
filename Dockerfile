# set base image (host OS)
FROM python:3.8-alpine

ENV USERID=
ENV ACCESSTOKEN=

WORKDIR /code

RUN mkdir outputs

VOLUME /code/outputs

COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps gcc musl-dev
RUN pip install -r requirements.txt
RUN apk del .build-deps gcc musl-dev

COPY main.py .

CMD [ "python", "./main.py" ]