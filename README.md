Sorting Hat [![Build Status](https://travis-ci.org/MetricsGrimoire/sortinghat.svg?branch=master)](https://travis-ci.org/MetricsGrimoire/sortinghat) [![Coverage Status](https://img.shields.io/coveralls/MetricsGrimoire/sortinghat.svg)](https://coveralls.io/r/MetricsGrimoire/sortinghat?branch=master)
===========

A tool to manage identities.

Usage
-----
```
sortinghat [--help] [-c <file>] [-u <user>] [-p <password>]
           [--host <host>] [--port <port>] [-d <name>]
           command [<cmd_args>]

The most commonly used sortinghat commands are:

    add         Add identities
    affiliate   Affiliate identities
    config      Get and set configuration parameters
    enroll      Enroll identities into organizations
    init        Create an empty registry
    load        Import data (i.e identities, organizations) on the registry
    merge       Merge unique identities
    mv          Move an identity into a unique identity
    log         List enrollment information available in the registry
    orgs        List, add or delete organizations and domains
    rm          Remove identities from the registry
    show        Show information about a unique identity
    withdraw    Remove identities from organizations

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

Configuration
-------------

* Configure database parameters
```
  $ sortinghat config set db.user <user>
  $ sortinghat config set db.password <password>
  $ sortinghat config set db.database <name>
```

* Initialize database
```
  $ sortinghat init <name>
```

Requirements
------------

* Python >= 2.7 (3.x series not supported yet)
* MySQL >= 5.5
* SQLAlchemy >= 0.8
* Jinja2 >= 2.7
* python-dateutil >= 1.5

License
-------

Licensed under GNU General Public License (GPL), version 3 or later.
