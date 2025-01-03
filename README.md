# Create docker setup form scratch

---

### App image

Use current directory as the build context to create the image based on the instructions  on the Dockerfile.
The image is also tagged `<app-name>`, so it can be easy to identify.
```
sudo docker build -t <app-name> .
```
 
Verify images
```
sudo docker image
```

**Before postgresql setup, deactivate virtual env and postgresql process**

```
deactivate
```

```
sudo systemctl stop postgresql
```

Now, created Docker network, wil facilitate communication between the 
Django application container and to PostgreSQL database

```
sudo docker network create <app-name-network>
```


Create actual PostgreSQL container with a user and specified password durin initialization

```
sudo docker run --name <app-server-name> -p 5432:5432 -e POSTGRES_USER=<USER> -e POSTGRES_PASSWORD=<PASSWORD> --network <app-name-network> -d postgres
```

Starting interactive bash console can be achieved with
```
sudo docker exec -t <image-name> bash
```

When accessing cmd via bash, it is required to create new database. It is possible to perform creation with default `psql` commands.

To create container for actual Django application, use
```
sudo docker run --env-file .env --name <django-app-name> -p 8000:8000 --network <app-network> -d <app-server-name>
```

Verify if containers are running with
```
sudo docker ps
```

Doing migrations and other django commands
```
sudo docker exec -it <django-app-name> python manage.py migrate
```

To restart docker image, use
```
sudo docker restart <django-app-name>
```

# Docker compose

---

Build images defined in `docker-compose.yml`
```
sudo docker compose build
```

To launch defined services

```
sudo docker compose up
```

To access shell

```
sudo docker compose run <service> bash
```

or just send single terminal commands like (just reference example)

```
sudo docker compose run <service> python manage.py migrate
```

To access interactive bash session for postgresql image use 

```
sudo docker compose exec <postgres-image> psql -U <postgres-user> -d <django-app>
```
