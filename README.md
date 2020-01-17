# Callisto: a Jupiter Notebook Gallery

This `django` app creates a website that interfaces with JupyterHub extensions to import and share Jupyter Notebooks.

Through the app:
- users can import their own `.ipynb` Notebook files
- Imported Notebooks are rendered right in the app and
  - can be liked
  - commented
- Notebooks in the gallery can be exported with a one-click solution into an existing Jupyter Hub installation.

That way it's easy to build a community around sharing and re-using notebooks. See below for some GIF examples:

![](/static/aboutgifs/notebook_import.gif)
**Sharing a notebook right from the Jupyter Notebook**

![](/static/aboutgifs/notebook_export.gif)
**Opening a notebook right from the Callisto**

## Requirements
For the whole setup to work your singleuser `JupyterHub` image needs to install & activate 3 extensions to Jupyter:

###(1) JupyterHub importer plugin

The plugin is developed at [cccs-is/callisto-nbimport](https://github.com/cccs-is/callisto-nbimport). 

Installation (to be run on a single-user JupyterHub server):
```
pip install --no-cache-dir git+http://github.com/cccs-is/callisto-nbimport 
jupyter serverextension enable --py callisto_nbimport --sys-prefix
```
###(2) JupyterHub exporter plugin for Lab environment
For notebooks run in a Lab environment, install plugin [cccs-is/callisto-nbshare](https://github.com/cccs-is/callisto-nbshare). 

Installation (to be run on a single-user JupyterHub server):
```
git clone http://github.com/cccs-is/callisto-nbshare
cd callisto-nbshare
pip install --no-cache-dir . 
jupyter labextension install  
```
###(3) JupyterHub exporter plugin for classic environment
For notebooks run in a classic notebook environment, install plugin [cccs-is/callisto-bundler](https://github.com/cccs-is/callisto-bundler). 

Installation (to be run on a single-user JupyterHub server):
```
pip install --no-cache-dir git+http://github.com/cccs-is/callisto-bundler 
jupyter bundlerextension enable --py callisto_bundler --sys-prefix 
```
### Add Callisto URL to JupyterHub
The 'JUPYTER_CALLISTO_URL' environment variable should be set on JupyterHub poiting to Callisto.
For example:
```
JUPYTER_CALLISTO_URL='localhost:5000'
```
## Deployment
The app is build to be deployed as a pod in a Kubernetes cluster.
 
- Use the included Dockerfile to build an image;
- Create a pod based on this image exposing port 5000;
- Create a service and an ingress to make application reachable.

In a development environment it can be run as a standalone Django app using
```
pyhton manage.py runserver 5000
```
making the local app accesible at `127.0.0.1:5000`.

### Authentication
The app is expected to run behind an authentication proxy, such as OAuth2 proxy.

The app does no user authentication itself, rather uses OAuth user token which comes
as a result of authentication performed by the proxy.
 
### Database
Data is stored in a database - PostreSQL for deployed app; local buil-in SQLite
for development.

For production environment set the following environment variables:
- CALLISTO_DATABASE_NAME
- CALLISTO_DATABASE_HOST
- CALLISTO_DATABASE_PORT
- CALLISTO_DATABASE_USER
- CALLISTO_DATABASE_PASSWORD

For development environment set the following environment variable:
```
CALLISTO_DEVELOPMENT = True
``` 
to direct the app to use built-in local SQLite database.



### Settings
The app requires several environment variables to specify authentication, JupyterHub connection, and database information.

What should be in the `.env` file:

```
# the usual stuff for a django app:
SECRET_KEY='secret_key_here'

# JupyterHub URL
JUPYTERHUB_URL = http://localhost:8888

# The expected audience in the OAuth2 authentication token
OAUTH_TOKEN_AUDIENCE='https://graph.windows.net'

# Source of the public keys used by the OAuth2 provider to sign tokens
OAUTH_PUBLIC_KEYS_URL='https://login.microsoftonline.com/common/discovery/keys'

# Callisto database connection info:
CALLISTO_DATABASE_NAME='callisto'
CALLISTO_DATABASE_HOST='localhost'
CALLISTO_DATABASE_PORT=5432
CALLISTO_DATABASE_USER='my_db_user'
CALLISTO_DATABASE_PASSWORD='my_db_password'

# Or, if this is a development environment:
#CALLISTO_DEVELOPMENT = True
