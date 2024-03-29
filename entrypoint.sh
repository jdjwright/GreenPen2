#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi
cd /usr/src/app || exit

# Apply any outstanding migrations
python manage.py migrate

# Update static files

python manage.py collectstatic --noinput

exec "$@"