# SortingHat Docker Image

SortingHat is a tool to manage identities and is part of GrimoireLab
platform.

For more information about GrimoireLab and SortingHat, please visit
our [website](https://chaoss.github.io/grimoirelab/).


## How to use this image

### Quickstart 

It is recommended to use [docker compose](https://docs.docker.com/compose/install/linux/) to create your SortingHat environment, but you can create it with docker commands too.

#### Docker compose (recommended)

To run a standalone SortingHat instance, you need git and docker compose to run the following commands:

```
git clone git@github.com:chaoss/grimoirelab-sortinghat.git
cd grimoirelab-sortinghat/docker
docker compose up
```

Then go to [localhost:8000](http://localhost:8000) and login with username and password `admin`.

#### Docker

These commands will start a SortingHat server container in developer mode
with a MySQL and Redis server containers. The service will run on an HTTP
server on `localhost:8000`. You can access it with credentials `admin:admin`.
Modify `SORTINGHAT_SUPERUSER_*` env vars, if you want different values.

```
$ docker network create sh

$ docker run --rm --net sh --name mysqldb -e 'MYSQL_ALLOW_EMPTY_PASSWORD=yes' mysql:8.0.22

$ docker run --rm --net sh --name redisdb redis:latest redis-server --appendonly yes

$ docker run --rm --net sh -p 8000:8000 --name sortinghat \
    -e 'SORTINGHAT_SECRET_KEY=secret' \
    -e 'SORTINGHAT_DB_HOST=mysqldb' \
    -e 'SORTINGHAT_REDIS_HOST=redisdb' \
    -e 'SORTINGHAT_SUPERUSER_USERNAME=admin' \
    -e 'SORTINGHAT_SUPERUSER_PASSWORD=admin' \
    -e 'SORTINGHAT_HTTP_DEV=0.0.0.0:8000' \
    -e 'SORTINGHAT_UWSGI_WORKERS=1' \
    -e 'SORTINGHAT_UWSGI_THREADS=4'
    grimoirelab/sortinghat --dev
```

To run a worker that will execute jobs, use the next command:

```
$ docker run --rm --net sh --name sortinghat-worker-1 \
    -e 'SORTINGHAT_SECRET_KEY=secret' \
    -e 'SORTINGHAT_DB_HOST=mysqldb' \
    -e 'SORTINGHAT_REDIS_HOST=redisdb' \
    grimoirelab/sortinghat-worker
```


## Building the image

The image requires that the SortingHat Python package is built and ready
in `dist` directory. You can build a new package running the next commands:

```
$ yarn --cwd ui build
$ poetry build
```

Once the package is ready, to build the images (server and worker),
run `docker build` command from the repository root directory.

```
$ docker build -f docker/server.dockerfile -t grimoirelab/sortinghat .

$ docker build -f docker/worker.dockerfile -t grimoirelab/sortinghat-worker .
```


## License

SortingHat is licensed under GNU General Public License (GPL), version 3
or later.

However, this image is based on the [Debian docker image](https://hub.docker.com/_/debian),
Check their [license information](https://www.debian.org/social_contract#guidelines)
for the type of software is contained in this image.
