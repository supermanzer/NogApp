#!/bin/bash

# Wait for Postgres to start
sleep 10

# Prepare any pending migrations
"./manage.py makemigrations"

# Apply any pending migrations
"./manage.py migrate"


