#!/bin/bash

HOST=
BACKUP_USER=
RESTORE_USER=
export PGPASSWORD=remote_password
PORT=
DATABASE=

dump_name=dump_`date +%d-%m-%Y"_c"%H_%M_%S`.tar

# Dump from remote into local

"/Applications/pgAdmin 4 2.app/Contents/SharedSupport/pg_dump"  --host $HOST  --port $PORT --username $BACKUP_USER --no-password  --verbose -Fc $DATABASE > $dump_name

docker-compose down
docker-compose up -d db
docker-compose exec db psql -U postgres -c "drop database $DATABASE"
docker-compose exec db psql -U postgres -c "create database $DATABASE"

# restore the dump from the previous part
docker exec -i greenpen2_db_1 pg_restore -U $RESTORE_USER -v -O -x -d $DATABASE < $dump_name

# restart system as normal

docker-compose down
