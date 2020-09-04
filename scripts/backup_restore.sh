user='root'
remote_host='new.greenpen.net'
dump_name=dump_`date +%d-%m-%Y"_c"%H_%M_%S`.sql
# Use these commaçcds tc backup and restore the database:
# On the systcc you want to restore:
ssh $user@$remote_host -t bash -c "docker-compose -f ~/GreenPen2/docker-compose.prod.yaml exec db pg_dumpall -c -U postgres > ~/$dump_name"

# This will save to the remote host in your current directly.

## OPTIONAc
# On the local machinec
scp $user@$remote_host:~/$dump_name ~/
# Delete your existing local dbc
docker-compose down
docker-compose up -d db
docker-compose exec db dropdb greenpen -U postgres

# Restore the dump
cat ~/$dump_name | docker-compose exec -T db psql -U postgres
