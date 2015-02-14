pydockerize
===========

Creates a Docker image from a Python app with a pip ``requirements.txt``
file

Given a Python app with a ``requirements.txt`` file, you can trivially
make it into a Docker image.

Usage
=====

::

    $ pydockerize --help
    Usage: pydockerize [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

      Create Docker images for Python apps

    Options:
      --version                   Show the version and exit.
      -b, --base-images TEXT      Base docker images (comma-separated list) -
                                  e.g.: "python:2.7-onbuild,python:3.4-onbuild".
                                  Conflicts with --python-versions.
      -c, --cmd TEXT              Command (CMD) to set in image. Conflicts with
                                  --procfile
      -e, --entrypoint TEXT       Entry point (ENTRYPOINT) to set in image
      -p, --python-versions TEXT  Python versions (comma-separated list) - e.g.:
                                  "2.7,3.4". Conflicts with --base-images.
      --procfile FILENAME         Procfile to get command from. Conflicts with
                                  --cmd.
      -t, --tag TEXT              Repository name (and optionally a tag) to be
                                  applied to the resulting image in case of
                                  success
      -r, --requirement PATH      pip requirements file with packages to install
      --help                      Show this message and exit.

    Commands:
      build        Run `docker build` with Dockerfile(s) from `generate`
      generate     Write Dockerfile(s)
      generatefig  Generate fig.yml for fig/Docker Compose (http://fig.sh).
      images       Show images for repo from --tag
      ps           List Docker containers
      run          Run a Docker container

Usage examples
==============

.. code:: bash

    # Assume requirements in requirements.txt.
    # Tags built image with directory name (lowercased).
    # Container CMD taken from Procfile by default.
    $ pydockerize build

    # Add a custom tag to built image
    $ pydockerize -t my_cool_app build

    # Specifies a requirements file
    $ pydockerize -r requirements-prod.txt build

    # Generate Dockerfile but don't build the image
    # Perhaps you want to commit the Dockerfile and have the image built later
    # by a CI server.
    $ pydockerize generate

    # Specify multiple Python versions to build Docker images for
    $ pydockerize --python-versions=2.7,3.4 build

    # Specify a custom command to invoke when running container
    # (Default is to get it from Procfile, if it exists)
    $ pydockerize --cmd="pserve app.ini" build

    # Show current images for app in current directory
    $ pydockerize images

    $ pydockerize run -d
    Invoking: docker run -it --name=inventorysvc -v /Users/marca/dev/surveymonkey/inventorysvc:/host -p 6200:6200 -d inventorysvc
    fe01097e6b7a35150afce19888b65ad94cd51c9cc256834a6bb22c7c88f881fc

    $ pydockerize ps
    CONTAINER ID        IMAGE                 COMMAND                CREATED             STATUS              PORTS                    NAMES
    fe01097e6b7a        inventorysvc:latest   "/bin/sh -c 'gunicor   42 seconds ago      Up 41 seconds       0.0.0.0:6200->6200/tcp   inventorysvc

Setting the ``CMD`` for image
=============================

There are several ways to set the ``CMD``:

1. Specify it with ``--cmd``.
2. Specify a (one-line) ``Procfile`` with ``--procfile`` and it will
   grab the command from there.
3. If you don't specify ``--cmd`` or ``--procfile``, but there is a
   ``Procfile`` present it will default to grabbing command from there.
