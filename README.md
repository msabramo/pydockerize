# pydockerize

Make a Docker container from a Python app with a pip `requirements.txt` file

# Usage examples

```bash
# Assume requirements in requirements.txt; doesn't tag build image
pydockerize

# Assumes requirements in requirements.txt
pydockerize -t my_cool_app

# Specifies a tag and a requirements file
pydockerize -t my_cool_app requirements-prod.txt
```
