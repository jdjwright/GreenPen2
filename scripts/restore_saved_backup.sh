#!/bin/bash

RESTORE_USER=postgres
DATABASE="greenpen"
# Oh no
dump_name=dump_04-08-2021_c17_30_38.tar


docker-compose down
docker-compose up -d db
docker-compose exec db psql -U postgres -c "drop database greenpen"
docker-compose exec db psql -U postgres -c "create database greenpen"

if [ $? -eq 0 ]
then
  echo "Created a fresh database."
else
  echo "Could not delete and refresh the database. Is docker-compse.yaml setup correctly?" >&2
  exit 1
fi

# restore the dump from the previous part
docker exec -i greenpen2_db_1 pg_restore -U $RESTORE_USER -v -O -x -d $DATABASE < $dump_name

if [ $? -eq 0 ]
then
  echo "Restored database successfully. Stopping docker..."
else
  echo "Could not restore the database. Check the backup files." >&2
  exit 1
fi
# restart system as normal

docker-compose down
