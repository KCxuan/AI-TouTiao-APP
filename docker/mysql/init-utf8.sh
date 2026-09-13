#!/bin/bash
set -e
echo "Importing seed data with utf8mb4..."
mysql --default-character-set=utf8mb4 -uroot -p"$MYSQL_ROOT_PASSWORD" < /opt/seed/database.sql
echo "Seed import finished."
