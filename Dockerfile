FROM python:3.5
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/requirements.txt
RUN apt-get update && \
    apt-get install -y locales && \
    apt-get install -y xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic && \
    apt-get install -y fonts-dejavu fonts-dejavu-core fonts-dejavu-extra && \
    locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
RUN pip install -r requirements.txt
ADD . /code
