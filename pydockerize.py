#!/usr/bin/env python

from __future__ import print_function

import contextlib
import os
import shutil
import subprocess
import sys
import textwrap

import click


DEFAULT_BASE_IMAGES = ['python:2.7-onbuild']


@click.command()
@click.version_option()
@click.option('-b', '--base-images',
              default=','.join(DEFAULT_BASE_IMAGES),
              help='Base docker images (comma-separated list) - e.g.: '
                   '"python:2.7-onbuild,python:3.4-onbuild"')
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
        filename = write_dockerfile(base_image, requirements_file)
        invoke_docker_build(tag, base_image, filename)

    print('\nShowing Docker images for %s:\n' % tag)
    show_docker_images(tag)
    print()


def write_dockerfile(base_image, requirements_file):
    print('write_dockerfile: base_image = %r' % base_image)
    dirname = '.'
    filename = os.path.join(dirname, 'Dockerfile-' + base_image)
    print('write_dockerfile: Writing %s' % filename)

    with open(filename, 'w+') as f:
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

    return filename


def invoke_docker_build(repo_and_tag, base_image, filename):
    print('invoke_docker_build: repo_and_tag = %r' % repo_and_tag)
    cmd = ['docker', 'build']
    if repo_and_tag:
        if ':' in repo_and_tag:
            raise Exception("':' in tag not supported yet")
        tag = get_tag_from_base_image(base_image)
        cmd.append('-t')
        cmd.append(repo_and_tag + ':' + tag)
    cmd.append('--file')
    cmd.append(filename)
    cmd.append('.')
    print('invoke_docker_build: Calling subprocess with cmd = %r' % cmd)
    status = subprocess.call(cmd)
    if status == 0:
        print('Docker build succeeded.')
    else:
        print('Docker build failed with %d' % status)


def show_docker_images(repo):
    cmd = ['docker', 'images', repo]
    return subprocess.call(cmd)


def get_tag_from_base_image(base_image):
    tag = base_image
    replacements = {'python:': 'py', '-onbuild': ''}

    for old, new in replacements.items():
        tag = tag.replace(old, new)

    return tag


if __name__ == '__main__':
    pydockerize()
