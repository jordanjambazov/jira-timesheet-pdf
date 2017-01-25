FROM python:3.5
RUN mkdir /code
WORKDIR /code
ADD . /code
RUN apt-get update
RUN pip install -r requirements.txt
