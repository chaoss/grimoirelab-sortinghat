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

Migration from "old" MetricsGrimoire identities
-----------------------------------------------

Assume we had a database named "project_scm", with information about the gi trepository of project "project", with the "old" MetricsGrimoire identities. The process to migrate to Sorting Hat is as follows (assuming sortinghat is already installed):

```
[Create the Sorting Hat database for "new" identities]
  $ sortinghat init project_ids
[For each data source of interest (SCM, ITS, MLS, etc.) export identities
 to a JSON file, and import it into the Sorting Hat database]
  $ mg2sh -d project_scm -s project:scm -o project-scm.json
  $ sortinghat -d project_ids load --identities  project-scm.json
  ... [Repeat previous two step per each data source, switching "scm"
       to "its", "mls", etc.]
[Export all the identities in the Sorting Hat database]
  $ sortinghat -d project_ids export --identities project-sh.json
[Create people2identities table for each data source database,
 using the identities exported in the previous step]
  $ sh2mg -d project_scm -s project:scm project-sh.json
[Transfer merged uids and company affiliation to sorting hat database]
  $ migrate.py -d project_scm -s project_ids -i project_scm -o
  ... [Repeat previous two steps per each data source, switching "scm"
       to "its", "mls",  etc. except in the "-i" parameter]
[Select a main identity for each merged identity]
  $ identifier2sh.py -d project_ids
```

Notes:

* migrate.py is in the VizGrimoireUtils repo, identities directory.
* All scripts need parameters to grant access to the databases, such the -u and -p (MySQL user and password) parameters.

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
