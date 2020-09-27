# Amendments from book

* to install the psycopg2-binary package you need the Visual Studio 14 build tools installed. 
* however, this package gave an error when trying to migrate the database. Had to uninstall and use the psycopg2 package instead, which worked.
* The requirements put the version of passlib at 1.7.1, but this gave an error loading the clock module that has been deprecated. Use version 1.7.1. The requirements.txt file is correct in this one.
* Exercise 21 uses the console to enter the Python code. However, when using db.session.add(user) you will get an error. This is because the Flask app needs to be in a context. Do this instead.

>>> app.app_context().push() 
>>> db.session.add(user) 
>>> db.session.commit()

All other db.session methods can run within the session without recreating a context.

A safer method is to use "with app.app_context()", however, you need to enter every command that uses the db.session as every context is different. Or copy information from contexts into variables for later use.