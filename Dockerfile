# set base image (host OS)
FROM python:3.8-alpine

ENV USERID=
ENV ACCESSTOKEN=
ENV REFRESHTOKEN=
ENV SLACKTOKEN=

WORKDIR /code

RUN mkdir outputs

VOLUME /code/outputs

COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps gcc musl-dev
RUN pip install -r requirements.txt
RUN apk del .build-deps gcc musl-dev

RUN apk add --no-cache curl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN mv ./kubectl /usr/local/bin


COPY main.py .

CMD [ "python", "./main.py" ]