# Sorting Hat [![build](https://github.com/chaoss/grimoirelab-sortinghat/actions/workflows/ci.yml/badge.svg?branch=muggle)](https://github.com/chaoss/grimoirelab-sortinghat/actions/workflows/ci.yml?query=workflow:build+branch:muggle+event:push)

**Warning**: This is the developing branch of the new version of Sorting Hat. We're moving Sorting Hat into a service.
The documentation below would be totally incorrect or inaccurate. 

## Description

A tool to manage identities.

Sorting Hat maintains an SQL database with identities coming (potentially) from different sources. Identities corresponding to the same real person can be merged in the same `individual`, with a unique uuid. For each individual, a profile can be defined, with the name and other data to show for the corresponding person by default.

In addition, each individual can be related to one or more affiliations, for different time periods. This will usually correspond to different organizations in which the person was employed during those time periods.

Sorting Hat is a part of the [GrimoireLab toolset](https://grimoirelab.github.io), which provides for Python modules and scripts to analyze data sources with information about software development, and allows to produce interactive dashboards to visualize that information.

In the context of GrimoireLab, Sorting Hat is usually run after data is retrieved with [Perceval](https://github.com/chaoss/grimmoirelab-perceval), to store the identities obtained into its database, and later merge them into individuals (and maybe affiliate them).

## Installation

### From source code

Clone the repository, and change to the `muggle` branch
```
$ git clone https://github.com/chaoss/grimoirelab-sortinghat
$ git checkout muggle
```

#### Backend

We use [Poetry](https://python-poetry.org/docs/) for managing the project.

Install the required dependencies (this will also create a virtual environment)
```
$ poetry install
```

Activate the virtual environment
```
$ poetry shell
```

Migrations and create a superuser
```
(.venv)$ ./manage.py makemigrations --settings=config.settings.devel
(.venv)$ ./manage.py migrate --settings=config.settings.devel
(.venv)$ ./manage.py createsuperuser --settings=config.settings.devel
```

Run SortingHat backend Django app:
```
(.venv)$ ./manage.py runserver --settings=config.settings.devel
```

#### Frontend

Install the required dependencies
```
$ cd ui/
$ yarn install
```

Run SortingHat frontend Vue app:
```
$ yarn serve
```

## Requirements

* Python >= 3.6
* Poetry >= 1.1.0
* MySQL >= 5.7 or MariaDB 10.0
* Django = 2.1
* Django-MySQL >= 3.2.0
* Graphene-Django >= 2.0

You will also need some other libraries for running the tool, you can find the
whole list of dependencies in [pyproject.toml](pyproject.toml) file.

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
$ yarn test:unit -u
```

## License

Licensed under GNU General Public License (GPL), version 3 or later.
