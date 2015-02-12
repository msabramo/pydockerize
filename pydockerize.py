#!/usr/bin/env python

import os
import subprocess
import sys
import textwrap

import click


DEFAULT_BASE_IMAGES = ['python:2-onbuild']


@click.command()
@click.version_option()
@click.option('-b', '--base-images',
              help='Base docker image')
@click.option('-t', '--tag',
              help='Repository name (and optionally a tag) to be applied to '
                   'the resulting image in case of success')
@click.argument('requirements_file', type=click.Path(exists=True),
                default='requirements.txt')
@click.pass_context
def pydockerize(ctx, requirements_file, tag, base_images=DEFAULT_BASE_IMAGES):
    """Create Docker images for Python apps"""
    print('requirements_file = %r' % requirements_file)
    print('tag = %r' % tag)
    for base_image in base_images.split(','):
        write_dockerfile(base_image)
    invoke_docker_build(tag)


def write_dockerfile(base_image):
    print('write_dockerfile: base_image = %r' % base_image)
    with open('Dockerfile', 'w') as f:
        f.write(textwrap.dedent("""\
            # This Docker image takes care of doing `pip install -r requirements.txt`
            # For more details on this Docker image, see: https://registry.hub.docker.com/_/python/
            FROM {base_image}

            # This is so one can mount a volume from the host to give the container access
            # to the host's current working directory.
            #
            # E.g.:
            #
            #   - `docker run -v $(pwd):/host` from command-line
            #         or
            #   - `volumes: [".:/host"]` in fig.yml
            WORKDIR /host
        """.format(base_image=base_image)))


def invoke_docker_build(tag):
    print('invoke_docker_build: tag = %r' % tag)
    cmd = ['docker', 'build']
    if tag:
        cmd.append('-t')
        cmd.append(tag)
    cmd.append('.')
    print('invoke_docker_build: Calling subprocess with cmd = %r' % cmd)
    status = subprocess.call(cmd)
    if status == 0:
        print('Docker build succeeded.')
    else:
        print('Docker build failed with %d' % status)


if __name__ == '__main__':
    pydockerize()
