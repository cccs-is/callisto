# A Jupiter Notebook Gallery: Juno's Exploratory

[![Build Status](https://travis-ci.org/gedankenstuecke/jupyter-gallery.svg?branch=master)](https://travis-ci.org/gedankenstuecke/jupyter-gallery)
[![Maintainability](https://api.codeclimate.com/v1/badges/65c9247d5e7293dc94da/maintainability)](https://codeclimate.com/github/gedankenstuecke/jupyter-gallery/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/65c9247d5e7293dc94da/test_coverage)](https://codeclimate.com/github/gedankenstuecke/jupyter-gallery/test_coverage)

This `django` app creates a website that interfaces with an external API (right now only with the one of Open Humans) to import Jupyter Notebooks.

Through the app:
- users can import their own `.ipynb` Notebook files
- Imported Notebooks are rendered right in the app and
  - can be liked
  - commented
- Notebooks in the gallery can be exported with a one-click solution into an existing Jupyter Hub installation.

That way it's easy to build a community around sharing and re-using notebooks. See below for some GIF examples:

![](/static/aboutgifs/sharing.gif)
**Sharing a notebook right from the Jupyter Notebook**

![](/static/aboutgifs/open.gif)
**Opening a notebook right from the Gallery**

## Requirements
For the whole setup to work your singleuser `JupyterHub` image needs to install & activate 3 extensions to Jupyter:

### custom bundler
A custom bundler is needed to add the `Share Notebook` menu item. It can be found at [gedankenstuecke/jupyter-bundler-openhumans](https://github.com/gedankenstuecke/jupyter-bundler-openhumans). An easy way to install the `bundler` and `nbextension` provided by this python package is:

```
git clone https://github.com/gedankenstuecke/jupyter-bundler-openhumans.git
cd jupyter-bundler-openhumans
pip install -e .
jupyter bundlerextension enable --py oh_bundler
jupyter nbextension install --py oh_bundler --sys-prefix
jupyter nbextension enable --py oh_bundler --sys-prefix
```

Per default the post-sharing redirect will lead to `http://127.0.0.1:5000/shared`. See the [repository](https://github.com/gedankenstuecke/jupyter-bundler-openhumans) for more details on the settings.

### custom URL handler
This handler is needed for accepting a file in the Jupyter setup when being pushed from the gallery app. The handler Python module is in [gedankenstuecke/jupyter-notebook-importer](https://github.com/gedankenstuecke/jupyter-notebook-importer). The easiest way to install it locally is:

```
git clone https://github.com/gedankenstuecke/jupyter-notebook-importer.git
cd jupyter-notebook-importer
pip install -e .
jupyter serverextension enable --py oh_notebook_importer
```

## Deployment
This app was build with the idea to be deployed to `heroku`. If you already have the `heroku` CLI installed all you should need to do to start the application locally is:

```
pipenv install --dev
pipenv shell
heroku local:run ./manage.py migrate
heroku local
```

Now your local heroku app should run and be accessible from `127.0.0.1:5000`

Most likely it will not work completely unless you have set up some `.env` file in this directory with the following settings:

### settings
what should be in the `.env` file:

```
# the usual stuff for a django app:
SECRET_KEY='secret_key_here'

# the only UNusual stuff:
# JupyterHub URL
JUPYTERHUB_URL = http://localhost:8888

# The expected audience in the OAuth2 authentication token
OAUTH_TOKEN_AUDIENCE='https://graph.windows.net'

# Source of the public keys used by the OAuth2 provider to sign tokens
OAUTH_PUBLIC_KEYS_URL='https://login.microsoftonline.com/common/discovery/keys'

