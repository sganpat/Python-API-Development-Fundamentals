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

