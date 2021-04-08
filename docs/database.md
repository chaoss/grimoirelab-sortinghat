## Database

The conceptual schema of the SortingHat database is shown below. Individuals are the first-class citizens. They have a profile, which summarizes the member data, and can be linked to more than one identity and organization, which are automatically extracted from the software development tools of your project. Note that organizations or identities can be easily excluded from SortingHat by registering their names/emails/usernames to a _matching blacklist_. The filter associated to the blacklist is executed every time an identity is inserted to the database or modified.

![sh-database-diagram](sh-database-diagram.svg)
