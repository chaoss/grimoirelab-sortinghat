# SortingHat Docker Image

SortingHat is a tool to manage identities and is part of GrimoireLab
platform.

For more information about GrimoireLab and SortingHat, please visit
our [website](https://chaoss.github.io/grimoirelab/).


## How to use this image

### Quickstart 

These commands will start a SortingHat server container in developer mode
with a MySQL server container. The server will run an HTTP server on
`localhost:8000`. You can access it with credentials `admin:admin`.
Modify `SORTINGHAT_SUPERUSER_*` env vars, if you want different values.

```
$ docker run --rm --net sh --name mysqldb -e 'MYSQL_ALLOW_EMPTY_PASSWORD=yes' mysql:8.0.22

$ docker run --rm --net sh -p 8000:8000 --name sortinghat \
    -e 'SORTINGHAT_SECRET_KEY=secret' -e 'SORTINGHAT_DB_HOST=mysqldb' \
    -e 'SORTINGHAT_SUPERUSER_USERNAME=admin' \
    -e 'SORTINGHAT_SUPERUSER_PASSWORD=admin' \
    -e 'SORTINGHAT_HTTP_DEV=0.0.0.0:8000' \
    grimoirelab:sortinghat --dev
```


## Building the image

The image requires that the SortingHat Python package is built and ready
in `dist` directory. You can build a new package running the next commands:

```
$ yarn --cwd ui build
$ poetry build
```

Once the package is ready, to build the image, run `docker build` command
from the repository root directory.

```
$ docker build -f docker/Dockerfile -t grimoirelab:sortinghat .
```


## License

SortingHat is licensed under GNU General Public License (GPL), version 3
or later. This image is based on Debian docker image. https://www.debian.org/social_contract#guidelines
