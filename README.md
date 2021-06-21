# Sorting Hat [![tests](https://github.com/chaoss/grimoirelab-sortinghat/workflows/tests/badge.svg?branch=muggle)](https://github.com/chaoss/grimoirelab-sortinghat/actions?query=workflow:tests+branch:muggle+event:push)

**Warning**: This is the developing branch of the new version of Sorting Hat. We're moving Sorting Hat into a service.
The documentation below would be totally incorrect or inaccurate. 

## Description

A tool to manage identities.

Sorting Hat maintains an SQL database with identities coming (potentially) from different sources. Identities corresponding to the same real person can be merged in the same `individual`, with a unique uuid. For each individual, a profile can be defined, with the name and other data to show for the corresponding person by default.

In addition, each individual can be related to one or more affiliations, for different time periods. This will usually correspond to different organizations in which the person was employed during those time periods.

Sorting Hat is a part of the [GrimoireLab toolset](https://grimoirelab.github.io), which provides for Python modules and scripts to analyze data sources with information about software development, and allows to produce interactive dashboards to visualize that information.

In the context of GrimoireLab, Sorting Hat is usually run after data is retrieved with [Perceval](https://github.com/chaoss/grimmoirelab-perceval), to store the identities obtained into its database, and later merge them into individuals (and maybe affiliate them).


## Requirements

* Python >= 3.6
* Poetry >= 1.1.0
* MySQL >= 5.7 or MariaDB 10.0
* Django = 3.1
* Graphene-Django >= 2.0

You will also need some other libraries for running the tool, you can find the
whole list of dependencies in [pyproject.toml](pyproject.toml) file.


## Installation

### Getting the source code

Clone the repository, and change to the `muggle` branch
```
$ git clone https://github.com/chaoss/grimoirelab-sortinghat
$ git checkout muggle
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
$ apt install libmariadbclient-dev
```

#### Installation and configuration

Install the required dependencies (this will also create a virtual environment).
```
$ poetry install
```

Activate the virtual environment:
```
$ poetry shell
```

Migrations, fixtures and create a superuser:
```
(.venv)$ ./manage.py makemigrations --settings=config.settings.devel
(.venv)$ ./manage.py migrate --settings=config.settings.devel
(.venv)$ ./manage.py loaddata sortinghat/core/fixtures/countries.json --settings=config.settings.devel
(.venv)$ ./manage.py createsuperuser --settings=config.settings.devel
```

#### Running the backend

Run SortingHat backend Django app:
```
(.venv)$ ./manage.py runserver --settings=config.settings.devel
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

#### Running the frontend

Run SortingHat frontend Vue app:
```
$ yarn serve
```

## Running tests

SortingHat comes with a comprehensive list of unit tests for both 
frontend and backend.

#### Backend test suite
```
(.venv)$ ./manage.py test --settings=config.settings.testing
```

#### Frontend test suite
```
$ cd ui/
$ yarn test:unit
```

## License

Licensed under GNU General Public License (GPL), version 3 or later.
