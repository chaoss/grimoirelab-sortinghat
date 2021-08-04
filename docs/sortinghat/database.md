# How is data stored in SortingHat

SortingHat maintains an SQL database with the identities coming from different sources. Identities corresponding to the same person can be merged into the same <code>individual</code>, with a unique uuid. For each individual, a profile can be defined, with the name and other data to show corresponding person by default.

The conceptual schema of the SortingHat database is shown below. Individuals are the first-class citizens. They have a profile, which summarizes the member data, and can be linked to more than one identity and organization, which are automatically extracted from the software development tools of your project. Note that organizations or identities can be easily excluded from SortingHat by registering their names/emails/usernames to a matching blacklist. The filter associated to the blacklist is executed every time an identity is inserted to the database or modified.

![sh-database-diagram](./sh-database-diagram.svg)
