#!/bin/bash

GIT_BRANCH=$1
REPO_DIR_NAME=$2
VENV_DIR_NAME=$3

WORKING_DIR="/var/www/${REPO_DIR_NAME}"
PYTHON="/opt/${VENV_DIR_NAME}/bin/python"

echo "Working directory set to: ${WORKING_DIR}"

sudo chown -R www-data:www-data ${WORKING_DIR}

cd "$WORKING_DIR" || { echo "Failed to change directory to $WORKING_DIR"; exit 1; }

echo "Pulling changes from {$GIT_BRANCH}"

sudo -u www-data git fetch
sudo -u www-data git checkout -f ${GIT_BRANCH}
sudo -u www-data git reset --hard origin/${GIT_BRANCH}

echo "Running migrations and other django specific commands.."

sudo -u www-data ${PYTHON} manage.py collectstatic --noinput
sudo -u www-data ${PYTHON} manage.py migrate

echo "Restart NGINX and Gunicorn"

sudo systemctl restart gunicorn
sudo systemctl restart gunicorn.socket
sudo systemctl restart gunicorn.service
sudo systemctl daemon-reload

sudo nginx -t
sudo systemctl restart nginx
