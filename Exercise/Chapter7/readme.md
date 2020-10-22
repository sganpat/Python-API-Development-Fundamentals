## Fixes

original version gave an error

* ImportError: cannot import name 'secure_filename' from 'werkzeug'

Resolved based on this post from StackOverFlow - https://stackoverflow.com/questions/61628503/flask-uploads-importerror-cannot-import-name-secure-filename

In flask_uploads.py

Change

> from werkzeug import secure_filename,FileStorage

to

> from werkzeug.utils import secure_filename
> from werkzeug.datastructures import  FileStorage


A better option was provided by: https://stackoverflow.com/questions/51229595/after-editing-a-locally-installed-package-in-heroku-it-resets

1- Fork the package repo on GitHub.

2- Edit it and change whatever you need.

3- Now remove the original package name from your requirments.txt and replace it with git+https://github.com/you-github-username/forked-edited-package.git

the GitHub package is updated with the correct settings though. 
