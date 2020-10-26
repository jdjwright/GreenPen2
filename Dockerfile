FROM python:3.8.0-alpine AS build-image

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev build-base  libffi-dev

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install --user -r requirements.txt
COPY . /usr/src/app/

# Set up deploy image



# copy project
COPY . /usr/src/app/
# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]