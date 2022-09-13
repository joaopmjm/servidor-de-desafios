#!/usr/bin/env sh

sqlite3 -batch "$PWD/data/database.sqlite" <"$PWD/docker/php/scripts/initdb.sql"

