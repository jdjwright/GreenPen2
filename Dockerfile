FROM python:3.8.0-buster AS build-image

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apt-get update

RUN apt-get -y install  build-essential libssl-dev libffi-dev python3-dev cargo netcat
# install dependencies
RUN pip install --upgrade pip setuptools wheel
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install --user -r requirements.txt

# copy project
COPY entrypoint.sh /usr/src/app/
COPY manage.py /usr/src/app/
COPY GreenPen/ /usr/src/app/GreenPen/
COPY jstree/ /usr/src/app/jstree/
COPY nginx/ /usr/src/app/nginx/

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]