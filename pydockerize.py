#!/usr/bin/env python

from __future__ import print_function

import os
import subprocess
import textwrap

import click


DEFAULT_BASE_IMAGES = ['python:2.7-onbuild']


@click.command()
@click.version_option()
@click.option('-b', '--base-images',
              default=None,
              help='Base docker images (comma-separated list) - e.g.: '
                   '"python:2.7-onbuild,python:3.4-onbuild". Conflicts with '
                   '--python-versions.')
@click.option('-c', '--cmd',
              help='Command (CMD) to set in image. Conflicts with --procfile')
@click.option('-e', '--entrypoint',
              help='Entry point (ENTRYPOINT) to set in image')
@click.option('-p', '--python-versions',
              default=None,
              help='Python versions (comma-separated list) - e.g.: '
                   '"2.7,3.4". Conflicts with --base-images.')
@click.option('--procfile', type=click.File(),
              help='Procfile to get command from. Conflicts with --cmd.')
@click.option('-t', '--tag',
              help='Repository name (and optionally a tag) to be applied to '
                   'the resulting image in case of success')
@click.argument('requirements_file', type=click.Path(exists=True),
                default='requirements.txt')
@click.pass_context
def pydockerize(ctx, requirements_file, tag, cmd, entrypoint, procfile,
                base_images=None, python_versions=None):
    """Create Docker images for Python apps"""

    if base_images is not None and python_versions is not None:
        raise Exception(
            'Cannot specify both --base-images and --python_versions')

    if base_images is not None:
        base_images = base_images.split(',')
    else:
        base_images = DEFAULT_BASE_IMAGES

    if python_versions is not None:
        python_versions = python_versions.split(',')
        base_images = get_base_images_from_python_versions(python_versions)

    if cmd is not None and procfile is not None:
        raise Exception('Cannot specify both --cmd and --procfile')

    if cmd is None and procfile is None and os.path.exists('Procfile'):
        procfile = open('Procfile')

    if procfile:
        cmd = get_cmd_from_procfile(procfile)

    base_images_and_filenames = write_dockerfiles(
        base_images, requirements_file, cmd, entrypoint)

    for base_image, filename in base_images_and_filenames:
        invoke_docker_build(tag, base_image, filename)

    if tag:
        print('\nShowing Docker images for %s:\n' % tag)
        show_docker_images(tag)


def write_dockerfiles(base_images, requirements_file, cmd, entrypoint):
    for base_image in base_images:
        filename = write_dockerfile(base_image, requirements_file,
                                    cmd, entrypoint)
        yield base_image, filename


def get_base_images_from_python_versions(python_versions):
    return ['python:%s-onbuild' % python_version
            for python_version in python_versions]


def get_cmd_from_procfile(procfile):
    lines = procfile.readlines()
    if len(lines) > 1:
        raise Exception(
            'Procfile with multiple lines not supported')
    return lines[0].split(':')[1].strip()


def write_dockerfile(base_image, requirements_file, cmd, entrypoint):
    print('write_dockerfile: base_image = %r' % base_image)
    print('write_dockerfile: requirements_file = %r' % requirements_file)
    print('write_dockerfile: cmd = %r' % cmd)
    print('write_dockerfile: entrypoint = %r' % entrypoint)

    filename = 'Dockerfile-' + base_image
    print('write_dockerfile: Writing %s' % filename)

    with open(filename, 'w+') as f:
        f.write(textwrap.dedent("""\
            # This Docker image takes care of doing:
            #
            #     pip install -r requirements.txt
            #
            # For more details on this Docker image, see:
            # https://registry.hub.docker.com/_/python/
            FROM {base_image}

            # This is so one can mount a volume from the host to give the
            # container access to the host's current working directory.
            #
            # E.g.:
            #
            #   - `docker run -v $(pwd):/host` from command-line
            #         or
            #   - `volumes: [".:/host"]` in fig.yml
            WORKDIR /host
        """.format(base_image=base_image)))
        if entrypoint:
            f.write("\nENTRYPOINT " + entrypoint)
        if cmd:
            f.write("\nCMD " + cmd)

    return filename


def invoke_docker_build(repo_and_tag, base_image, filename):
    print('invoke_docker_build: repo_and_tag = %r' % repo_and_tag)
    cmd = ['docker', 'build']
    if repo_and_tag:
        if ':' in repo_and_tag:
            raise Exception("':' in tag not supported yet")
        tag = get_tag_from_base_image(base_image)
        cmd.append('--tag')
        cmd.append(repo_and_tag + ':' + tag)
    cmd.append('--file')
    cmd.append(filename)
    cmd.append('.')
    print('invoke_docker_build: Calling subprocess with cmd = %r\n'
          % ' '.join(cmd))
    status = subprocess.call(cmd)
    if status == 0:
        print('Docker build succeeded.')
    else:
        print('Docker build failed with %d' % status)
        raise click.Abort()


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
