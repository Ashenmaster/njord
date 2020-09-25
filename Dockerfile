# set base image (host OS)
FROM python:3.8-alpine

ENV USERID=
ENV ACCESSTOKEN=

WORKDIR /code

RUN mkdir outputs

VOLUME /code/outputs

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY main.py .

CMD [ "python", "./main.py" ]