####################################
# NGINX Container Dockerfile
# This file defines the Docker container that will run
# Nginx as our reverse proxy server
####################################

FROM nginx:1.29-alpine


RUN apk update && apk upgrade && \
    rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d