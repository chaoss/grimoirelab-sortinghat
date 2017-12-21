# Sorting Hat [![Build Status](https://travis-ci.org/grimoirelab/sortinghat.svg?branch=master)](https://travis-ci.org/grimoirelab/sortinghat) [![Coverage Status](https://img.shields.io/coveralls/grimoirelab/sortinghat.svg)](https://coveralls.io/r/grimoirelab/sortinghat?branch=master)

## Description

A tool to manage identities.

Sorting Hat maintains an SQL database with identities coming (potentially) from different sources. Identities corresponding to the same real person can be merged in the same unique identity, with a unique uuid. For each unique identity, a profile can be defined, with the name and other data to show for the corresponding person by default.

In addition, each unique identity can be related to one or more affiliations, for different time periods. This will usually correspond to different organizations in which the person was employed during those time periods.

Sorting Hat is a part of the [GrimoireLab toolset](https://grimoirelab.github.io), which provides for Python modules and scripts to analyze data sources with information about software development, and allows to produce interactive dashboards to visualize that information.

In the context of GrimoireLab, Sorting Hat is usually run after data is retrieved with [Perceval](https://github.com/grimmoirelab/perceval), to store the identities obtained into its database, and later merge them into unique identities (and maybe affiliate them).

## Source code and contributions

All the source code is available in the [Sorting Hat GitHub repository](https://github.com/grimoirelab/sortinghat). Please, upload pull requests if you have proposals to change the source code, and open an issue if you want to report a bug, ask for a new feature, or just comment something.

## Usage

```
usage: sortinghat [--help] [-c <file>] [-u <user>] [-p <password>]
                  [--host <host>] [--port <port>] [-d <name>]
                  command [<cmd_args>]

The most commonly used sortinghat commands are:

    add          Add identities
    affiliate    Affiliate identities
    autoprofile  Auto complete profiles
    blacklist    List, add or delete entries from the blacklist
    config       Get and set configuration parameters
    countries    List information about countries
    enroll       Enroll identities into organizations
    export       Export data (i.e identities) from the registry
    init         Create an empty registry
    load         Import data (i.e identities, organizations) on the registry
    merge        Merge unique identities
    mv           Move an identity into a unique identity
    log          List enrollment information available in the registry
    orgs         List, add or delete organizations and domains
    profile      Edit profile
    rm           Remove identities from the registry
    show         Show information about a unique identity
    unify        Merge identities using a matching algorithm
    withdraw     Remove identities from organizations

General options:
  -h, --help            show this help message and exit
  -c FILE, --config FILE
                        set configuration file
  -u USER, --user USER  database user name
  -p PASSWORD, --password PASSWORD
                        database user password
  -d DATABASE, --database DATABASE
                        name of the database where the registry will be stored
  --host HOST           name of the host where the database server is running
  --port PORT           port of the host where the database server is running

Run 'sortinghat <command> --help' to get information about a specific command.
```

## Installation

### From pypi

You can install sortinghat as a package from the pypi repository:

```
$ pip install sortinghat
```

### Native

You can install sortinghat just by running setup.py script:

```
$ python setup.py install
```

This will install it in the python default directories in your system.

If you don't install sortinghat with root privileges, or don't want to install it in the default directories, you can also use the source code directory, as cloned from the main git repo. It is enough to
configure your `$PATH` and `$PYTHONPATH` so that sortinghat, and the Python modules it needs, are found.

Add to your `$PATH` the directory which contains the sortinghat executables:

```
$ export PATH=$PATH:sortinghatdir/bin
```

In `$PYHTONPATH`, you need to include sortinghat as well. If sortinghatdir is the path where sortinghat is installed:

```
$ export PYTHONPATH=$PYTHONPATH:sortinghatdir
```

You are ready to use sortinghat!

### Docker

You can use our image from [DockerHub](https://hub.docker.com/r/grimoirelab/sortinghat/) (`grimoirelab/sortinghat`) and skip the `docker build` step.
If you prefer to build the image yourself execute:

```sh
$ docker build -t grimoirelab/sortinghat .
```

Next step would be to start a MySQL docker container for data storage:

```sh
$ docker run --name mysql \
             -e MYSQL_ROOT_PASSWORD=sortinghat \
             -d mysql
```

Run the sortinghat docker container in interactive mode:

```sh
$ docker run -i -t --rm \
             --link mysql:mysql \
             -e SORTINGHAT_DB_HOST=mysql \
             -e SORTINGHAT_DB_PASSWORD=sortinghat \
             -e SORTINGHAT_DB_DATABASE=sortinghat \
             grimoirelab/sortinghat \
             /bin/bash
```

Now you can initialize sortinghat with the database name `sortinghat`:

```
$ sortinghat init sortinghat
```

You are ready to use sortinghat and explore the commands documented below.
Have fun!

## Configuration

Set the database parameters via the `config` command:

```
  $ sortinghat config set db.host <mysql-host>
  $ sortinghat config set db.user <user>
  $ sortinghat config set db.password <password>
  $ sortinghat config set db.database <name>
  $ sortinghat config set db.port <port>
```

Alternatively you can set environment variables:

```
  $ export SORTINGHAT_DB_HOST=<mysql-host>
  $ export SORTINGHAT_DB_USER=<user>
  $ export SORTINGHAT_DB_PASSWORD=<password>
  $ export SORTINGHAT_DB_DATABASE=<name>
  $ export SORTINGHAT_DB_PORT=<port>
```

After this initialize a new database:

```
  $ sortinghat init <name>
```

## Compatibility between versions

SortingHat databases previous to 0.5.0 are no longer compatible. The
database schema changed in `uidentites` and `identities` tables to add the
field `last_modified` to log when a record was updated.

The next MySQL statements should be run to update the schema

```
mysql> ALTER TABLE uidentities ADD COLUMN last_modified DATETIME(6) DEFAULT NULL
mysql> ALTER TABLE identities ADD COLUMN last_modified DATETIME(6) DEFAULT NULL
```

SortingHat databases previous to 0.3.0 are no longer compatible. The
seed used to generate identities UUIDs changed and for that reason, these
ids should be re-generated.

The next steps will restore the database generating new UUIDs for each identity
but keeping the data and relationships between them.

1. Export data
```
$ sortinghat export --orgs orgs.json
$ sortinghat export --identities identities.json
```
1. Remove the database and/or create a new one with `sortinghat init`
1. Load data, this will regenerate the UUIDs
```
$ sortinghat load orgs.json
$ sortinghat load identities.json
```

## Basic commands

* Add some unique identities
```
  $ sortinghat add --name "John Smith" --email "jsmith@example.com" --username "jsmith" --source scm
  New identity a9b403e150dd4af8953a52a4bb841051e4b705d9 to a9b403e150dd4af8953a52a4bb841051e4b705d9

  $ sortinghat add --name "John Doe" --email "jdoe@example.com" --source scm
  New identity 3de180633322e853861f9ee5f50a87e007b51058 added to 3de180633322e853861f9ee5f50a87e007b51058
```

* Set a profile
```
  $ sortinghat profile --name "John Smith" --email "jsmith@example.com" --country US a9b403e150dd4af8953a52a4bb841051e4b705d9
  unique identity a9b403e150dd4af8953a52a4bb841051e4b705d9

  Profile:
      * Name: John Smith
      * E-Mail: jsmith@example.com
      * Bot: No
      * Country: US - United States of America
```

* Add an identity to an existing unique identity
```
  $ sortinghat add --username "jsmith" --source mls --uuid a9b403e150dd4af8953a52a4bb841051e4b705d9
  New identity 2612aad107cae121b45c1f46041650abc8e39421 added to a9b403e150dd4af8953a52a4bb841051e4b705d9
```

* Merge two identities
```
  $ sortinghat merge a7637bb1737bc2a83f3a3e25b9b441cba62d97c2 a9b403e150dd4af8953a52a4bb841051e4b705d9
  Unique identity 3de180633322e853861f9ee5f50a87e007b51058 merged on a9b403e150dd4af8953a52a4bb841051e4b705d9
```

* Move an identity into a unique identity
```
  $ sortinghat mv 3de180633322e853861f9ee5f50a87e007b51058 3de180633322e853861f9ee5f50a87e007b51058
  New unique identity 3de180633322e853861f9ee5f50a87e007b51058 created. Identity moved
```

* Remove a unique identity
```
  $ sortinghat rm 3de180633322e853861f9ee5f50a87e007b51058
  Unique identity 3de180633322e853861f9ee5f50a87e007b51058 removed
```

* Show identities information
```
  $ sortinghat show
  unique identity a9b403e150dd4af8953a52a4bb841051e4b705d9

  Profile:
      * Name: John Smith
      * E-Mail: jsmith@example.com
      * Bot: No
      * Country: US - United States of America

  Identities:
    2612aad107cae121b45c1f46041650abc8e39421	-	-	jsmith	mls
    a9b403e150dd4af8953a52a4bb841051e4b705d9	John Smith	jsmith@example.com	jsmith	scm

  No enrollments
```

* Add some organizations
```
  $ sortinghat orgs -a Example
  $ sortinghat orgs -a Bitergia
  $ sortinghat orgs -a Individual
```

* Add some domains to the organizations
```
  $ sortinghat orgs -a Example example.com --top-domain
  $ sortinghat orgs -a Example web.example.com
  $ sortinghat orgs -a Bitergia bitergia.com --top-domain
```

* List organizations
```
  $ sortinghat orgs
  Bitergia	bitergia.com *
  Example	example.com *
  Example	web.example.com
  Individual
```

* Remove domains
```
  $ sortinghat orgs -d Example web.example.com
```

* Remove organizations
```
 $ sortinghat orgs -d Bitergia
```

* Enroll
```
  $ sortinghat enroll --from 2014-06-01 --to 2015-09-01 a9b403e150dd4af8953a52a4bb841051e4b705d9 Example
  $ sortinghat enroll --from 2015-09-01 a9b403e150dd4af8953a52a4bb841051e4b705d9 Individual
```

* Show enrollments information
```
  $ sortinghat show a9b403e150dd4af8953a52a4bb841051e4b705d9
  unique identity a9b403e150dd4af8953a52a4bb841051e4b705d9

  Profile:
      * Name: John Smith
      * E-Mail: jsmith@example.com
      * Bot: No
      * Country: US - United States of America

  Identities:
    2612aad107cae121b45c1f46041650abc8e39421	-	-	jsmith	mls
    a9b403e150dd4af8953a52a4bb841051e4b705d9	John Smith	jsmith@example.com	jsmith	scm

  Enrollments:
    Example	2014-06-01 00:00:00	2015-09-01 00:00:00
    Individual	2015-09-01 00:00:00	2100-01-01 00:00:00
```

* Withdraw
```
  $ sortinghat withdraw --from 2014-06-01 --to 2015-09-01 a9b403e150dd4af8953a52a4bb841051e4b705d9 Example
```

## Import / Export

* Import data from a Sorting Hat JSON file
```
  $ sortinghat load sh.json
  Loading blacklist...
  Entry  added to the blacklist
  1/1 blacklist entries loaded
  Loading unique identities...
  + 00000ba7f563234e5f239e912f2df1021695122e (old 00000ba7f563234e5f239e912f2df1021695122e) loaded
  + 00003e37e7586be36c64ce4f9eafa89f11be2448 (old 00003e37e7586be36c64ce4f9eafa89f11be2448) loaded
  ...
  + fa84729382093928570aef849483948489238498 (old fa84729382093928570aef849483948489238498) loaded
  100/100 unique identities loaded
```

* Export identities
```
  $ sortinghat export --identities sh_ids.json
```

* Export organizations
```
  $ sortinghat export --orgs sh_orgs.json
```

## Requirements

* Python 2.7 and >= 3.4
* MySQL >= 5.5
* SQLAlchemy >= 1.0.0
* Jinja2 >= 2.7
* python-dateutil >= 2.6
* python-yaml >= 3.12

You will also need a MySQL Python driver to connect with the database server. We recommend to use one these packages:

* MySQLdb (only available for Python 2.7)
* PyMySQL

Optionally, you can install Pandas library to speed up the matching process:

* python-pandas >= 0.15

## License

Licensed under GNU General Public License (GPL), version 3 or later.
