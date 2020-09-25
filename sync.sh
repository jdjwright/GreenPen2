#!/bin/bash

HOST=new.greenpen.net
USER=root
dump_name=dump_`date +%d-%m-%Y"_c"%H_%M_%S`.sql

# Dump from remote into local

ssh  $USER@$HOST -T  "docker-compose -f GreenPen2/docker-compose.prod.yaml exec -T db pg_dumpall -c -U postgres" \
 > $dump_name

# Flush current db on local machine

docker-compose down
docker-compose up -d db
docker-compose exec db psql -U postgres -c "drop database greenpen"

# restore the dump from the previous part
cat $dump_name | docker exec -i greenpen_db_1 psql -U postgres

# restart system as normal

docker-compose down

