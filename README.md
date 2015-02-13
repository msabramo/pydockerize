# pydockerize

Creates a Docker image from a Python app with a pip `requirements.txt` file

Given a Python app with a `requirements.txt` file, you can trivially
make it into a Docker image.

# Usage examples

```bash
# Assume requirements in requirements.txt; doesn't tag build image
pydockerize

# Add a tag to built image
pydockerize -t my_cool_app

# Specifies a requirements file
pydockerize -t my_cool_app requirements-prod.txt

# Specify multiple Python versions to build Docker images for
pydockerize.py -t my_cool_app --python-versions 2.7,3.4

# Specify a command to invoke when running container
pydockerize.py -t my_cool_app --cmd "pserve app.ini"
```
