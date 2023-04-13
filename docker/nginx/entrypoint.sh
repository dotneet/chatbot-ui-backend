#!/bin/bash -ue -o pipefail

envsubst '${FRONTEND_HOST} ${BACKEND_HOST}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

nginx -g "daemon off;"
