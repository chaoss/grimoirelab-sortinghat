# Sorting Hat [![tests](https://github.com/chaoss/grimoirelab-sortinghat/workflows/tests/badge.svg)](https://github.com/chaoss/grimoirelab-sortinghat/actions?query=workflow:tests+branch:main+event:push) [![PyPI version](https://badge.fury.io/py/sortinghat.svg)](https://badge.fury.io/py/sortinghat)

## Description

A tool to manage identities.

Sorting Hat maintains an SQL database of unique identities of communities members across (potentially) many different sources. Identities corresponding to the same real person can be merged in the same `individual`, with a unique uuid. For each individual, a profile can be defined, with the name and other data shown for the corresponding person by default.

In addition, each individual can be related to one or more affiliations, for different time periods. This will usually correspond to different organizations in which the person was employed during those time periods.

Sorting Hat is a part of the [GrimoireLab toolset](https://grimoirelab.github.io), which provides Python modules and scripts to analyze data sources with information about software development, and allows the production of interactive dashboards to visualize that information.

In the context of GrimoireLab, Sorting Hat is usually run after data is retrieved with [Perceval](https://github.com/chaoss/grimoirelab-perceval), to store the identities obtained into its database, and later merge them into individuals (and maybe affiliate them).


## Requirements

* Python >= 3.9
* Poetry >= 1.1.0
* MySQL >= 8.1 or MariaDB >= 10.4
* Django = 4.2
* Graphene-Django >= 2.0
* uWSGI >= 2.0

You will also need some other libraries for running the tool, you can find the
whole list of dependencies in [pyproject.toml](pyproject.toml) file.


## Installation

### Getting the source code

To install from the source code you will need to clone the repository first:
```
$ git clone https://github.com/chaoss/grimoirelab-sortinghat
$ cd grimoirelab-sortinghat
```

### Backend

#### Prerequisites

##### Poetry

We use [Poetry](https://python-poetry.org/docs/) for managing the project.
You can install it following [these steps](https://python-poetry.org/docs/#installation).

##### mysql_config

Before you install SortingHat tool you might need to install `mysql_config`
command. If you are using a Debian based distribution, this command can be
found either in `libmysqlclient-dev` or `libmariadbclient-dev` packages
(depending on if you are using MySQL or MariaDB database server). You can
install these packages in your system with the next commands:

* **MySQL**

```
$ apt install libmysqlclient-dev
```

* **MariaDB**

```
$ apt install libmariadbclient-dev-compat
```

#### Installation and configuration

**Note**: these examples use `sortinghat.config.settings` configuration file.
In order to use that configuration you need to define the environment variable
`SORTINGHAT_SECRET_KEY` with a secret. More info
[here](https://docs.djangoproject.com/en/4.2/ref/settings/#std:setting-SECRET_KEY).


Install the required dependencies (this will also create a virtual environment).
```
$ poetry install
```

Activate the virtual environment:
```
$ poetry shell
```

Database creation, apply migrations and fixtures, deploy static files,
and create a superuser:
```
(.venv)$ sortinghat-admin --config sortinghat.config.settings setup
```

#### Running the backend

Run SortingHat backend Django app:
```
(.venv)$ ./manage.py runserver --settings=sortinghat.config.settings
```

### Frontend

#### Prerequisites

##### yarn

To compile and run the frontend you will need to install `yarn` first.
The latest versions of `yarn` can only be installed with `npm` - which
is distributed with [NodeJS](https://nodejs.org/en/download/).

When you have `npm` installed, then run the next command to install `yarn`
on the system:

```
npm install -g yarn
```

Check the [official documentation](https://yarnpkg.com/getting-started)
for more information.

#### Installation and configuration

Install the required dependencies
```
$ cd ui/
$ yarn install
```

#### Running the frontend on development mode

Run SortingHat backend Django app:
```
(.venv)$ ./manage.py runserver --settings=config.settings.devel
```

Build the frontend and watch for changes:
```
$ yarn watch --api_url=http://localhost:8000/api/ --publicpath="/static/" --mode development
```


## SortingHat service

Starting at version 0.8, SortingHat is released with a server app. The server has two
modes, `production` and `development`.

When `production` mode is active, a WSGI app is served. The idea is to use a reverse
proxy like NGINX or similar, that will be connected with the WSGI app to provide
an interface HTTP.

When `development` mode is active, an HTTP server is launched, so you can interact
directly with SortingHat using HTTP requests. Take into account this mode is not
suitable nor safe for production.

You will need a django configuration file to run the service. The file must be accessible
via `PYTHONPATH` env variable. You can use the one delivered within the SortingHat
package (stored in `sortinghat/config` folder) and modify it with your parameters.
Following examples will make use of that file.

In order to run the service for the first time, you need to execute the next commands:

Build the UI interface:
```
$ cd ui
$ yarn install
$ yarn build --mode development
```
If you want to run the UI at `/identities` run (you need to use the server 
behind a proxy server):
```
$ yarn build
```

Set a secret key:
```
$ export SORTINGHAT_SECRET_KEY="my-secret-key"
```

Set up the service creating a database, deploying static files,
and adding a superuser to access the app:
```
$ sortinghat-admin --config sortinghat.config.settings setup
```

Run the server (use `--dev` flag for `development` mode):
```
$ sortinghatd --config sortinghat.config.settings
```

By default, this runs a WSGI server in `127.0.0.1:9314`. The `--dev` flag runs
a server in `127.0.0.1:8000`.

You will also need to run some workers to execute tasks like recommendations
or affiliation. To start a worker run the command:
```
$ sortinghatw --config sortinghat.config.settings
```

To start a worker that processes jobs from a set of tenants when
`dedicated_queue` is active (see [below](#multi-tenancy))
use the next command:
```
$ sortinghatw --config sortinghat.config.settings tenant_A tenant_B
```

## Create new accounts
To create new accounts for SortingHat use the following command:

```
(.venv)$ sortinghat-admin create-user

Usage: sortinghat-admin create-user [OPTIONS]

  Create a new user given a username and password

Options:
  --username TEXT   Specifies the login for the user.
  --is-admin        Specifies if the user is superuser.
  --no-interactive  Run the command in no interactive mode.
```

## Assign users to permission groups
A user in a group automatically has the permissions granted to that group. To assign users to a permission group use the following command:
```
$ sortinghat-admin set-user-permissions username group
```

The list of groups can be customized using the configuration file `sortinghat/config/permission_groups.json`. You can use a different json file using the environment variable `SORTINGHAT_PERMISSION_GROUPS_LIST_PATH`.


## Compatibility between versions

### SortingHat 0.8.0 and GrimoireLab 0.8.0

SortingHat 0.7.x is no longer supported. Any database using this version will not work.

SortingHat databases 0.7.x are no longer compatible. The `uidentities` table was renamed
to `individuals`. The database schema changed in all tables to add the fields `created_at`
and `last_modified`. Also in `domains`, `enrollments`, `identities`, `profiles` tables,
there are some specific changes to the column names:
  * `domains`
    * `organization_id` to `organization`
  * `enrollments`
    * `organization_id` to `organization`
    * `uuid` to `individual`
  * `identities`
    * `uuid` to `individual`
  * `profiles`
    * `country_code` to `country`
    * `uuid` to `individual`

Please update your database running the following command:
```
$ sortinghat-admin --config sortinghat.config.settings migrate-old-database
```

### SortingHat 1.1.0 and GrimoireLab 1.3.0

SortingHat 1.1.0 allows the assignment of users to permission groups. By default, any
existing user in the database will have the minimum permissions, which will allow
only read access. To explicitly assign a user to a permission group, run the
command provided in the previous section 
[Assign users to permission groups](#assign-users-to-permission-groups)

## Multi-tenancy

SortingHat allows hosting multiple instances with a single service having each
instance's data isolated in different databases.

To enable this feature follow these guidelines:
- Set `MULTI_TENANT` settings to `True`.
- Define a list of tenants using the configuration file `sortinghat/config/tenants.json`.
  You can use a different json file using the environment variable 
  `SORTINGHAT_MULTI_TENANT_LIST_PATH`. The file should have the next schema:

  ```json
  {
    "tenants": [
      {"name": "tenant A", "dedicated_queue": true},
      {"name": "tenant B", "dedicated_queue": false}
    ]
  }
  ```

  Where `name` is the name of each tenant and `dedicated_queue`
  is a boolean value to set whether jobs will be run on a specific
  queue with the same tenant name.
- Assign users to tenants with the following command:
  `sortinghat-admin set-user-tenant username header tenant`
- The selected tenant should be included in the request using the
  `sortinghat-tenant` header.

There are some limitations:

- `default` database is only used to store users information and relations between
  users and databases, it won't store anything else related with SortingHat models.
- Usernames are shared across all instances, which means that it is not possible
  to have the same username with two different passwords in different instances.
- Tenants with `dedicated_queue` set as active will add their jobs to the queue
  of the same name. Queues will be created by SortingHat but, you will have
  to run a worker that processes that query.


## Running tests

SortingHat comes with a comprehensive list of unit tests for both 
frontend and backend.

#### Backend test suite
```
(.venv)$ ./manage.py test --settings=config.settings.config_testing
(.venv)$ ./manage.py test --settings=config.settings.config_testing_tenant
```

#### Frontend test suite
```
$ cd ui/
$ yarn test:unit
```

## License

Licensed under GNU General Public License (GPL), version 3 or later.
