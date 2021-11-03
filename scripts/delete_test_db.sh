#!/bin/bash
# Delete the testing database if PyCharm quits before it has
# a chance to delete it.

# docker-compose down
docker-compose up -d db
docker-compose exec db psql -U postgres -c "drop database test_greenpen"

# restart system as normal

# docker-compose down

