#!/usr/bin/env python

import os
import subprocess
import textwrap

import click


DEFAULT_BASE_IMAGES = ['python:2.7']


@click.group(chain=True)
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
@click.option('-r', '--requirement',
              'requirements_file', type=click.Path(exists=True),
              default='requirements.txt',
              help='pip requirements file with packages to install')
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

    if tag is None:
        tag = os.path.basename(os.getcwd()).lower()

    ctx.obj = {
        'base_images': base_images,
        'requirements_file': requirements_file,
        'cmd': cmd,
        'procfile': procfile,
        'entrypoint': entrypoint,
        'tag': tag,
    }


@pydockerize.command()
@click.pass_context
def generate(ctx):
    """Write Dockerfile(s)"""

    base_images = ctx.obj['base_images']
    requirements_file = ctx.obj['requirements_file']
    cmd = ctx.obj['cmd']
    procfile = ctx.obj['procfile']
    entrypoint = ctx.obj['entrypoint']

    if cmd is not None and procfile is not None:
        raise Exception('Cannot specify both --cmd and --procfile')

    if cmd is None and procfile is None and os.path.exists('Procfile'):
        procfile = open('Procfile')

    if procfile:
        cmd = get_cmd_from_procfile(procfile)
        click.echo('generate: Got cmd from %s => %r' % (procfile.name, cmd))
    else:
        click.echo('generate: cmd = %r' % cmd)

    click.echo('generate: entrypoint = %r' % entrypoint)
    click.echo('generate: base_images = %r' % base_images)
    click.echo('generate: requirements_file = %r' % requirements_file)

    base_images_and_filenames = []

    for base_image in base_images:
        filename = get_filename_from_base_image(base_image, base_images)
        generate_one(base_image, requirements_file, filename, cmd, entrypoint)
        base_images_and_filenames.append((base_image, filename))

    ctx.obj['base_images_and_filenames'] = base_images_and_filenames


def get_base_images_from_python_versions(python_versions):
    return ['python:%s-onbuild' % python_version
            for python_version in python_versions]


def get_cmd_from_procfile(procfile):
    lines = procfile.readlines()
    if len(lines) > 1:
        raise Exception(
            'Procfile with multiple lines not supported')
    return lines[0].split(':')[1].strip()


def generate_one(base_image, requirements_file, filename, cmd, entrypoint):
    click.echo('generate_one: base_image = %r' % base_image)
    click.echo('generate_one: Writing %s' % filename)

    with open(filename, 'w+') as f:
        f.write(textwrap.dedent("""\
            # This is a Dockerfile
            # Dockerfile reference: https://docs.docker.com/reference/builder/

            FROM {base_image}

            RUN mkdir -p /usr/src/app
            WORKDIR /usr/src/app

            # Install necessary Python packages from pip requirements file
            # requirements files: http://bit.ly/pip-requirements-files
            COPY {requirements_file} /usr/src/app/
            RUN pip install -r {requirements_file}

            # This is so one can mount a volume from the host to give the
            # container access to the host's current working directory. E.g.:
            #
            #   - `docker run -v $(pwd):/host` from command-line or ...
            #   - `volumes: [".:/host"]` in fig.yml
            WORKDIR /host
        """.format(base_image=base_image,
                   requirements_file=requirements_file)))
        if entrypoint:
            f.write("\nENTRYPOINT %s\n" % entrypoint)
        if cmd:
            f.write("\nCMD %s\n" % cmd)

    return filename


@pydockerize.command(
    short_help="Run `docker build` with Dockerfile(s) from `generate`")
@click.pass_context
def build(ctx):
    """Run `docker build` with Dockerfile(s) from `generate`"""

    tags_built = []
    tag = ctx.obj['tag']
    base_images = ctx.obj['base_images']

    click.echo("build: tag = '%s'" % tag)

    if no_dockerfiles_already_exist(base_images):
        ctx.invoke(generate)

    for base_image in base_images:
        filename = get_filename_from_base_image(base_image, base_images)
        tag_built = build_one(tag, base_image, base_images, filename)
        tags_built.append(tag_built or '<No tag>')

    click.secho('build: %d Docker build(s) succeeded: %s'
                % (len(base_images), ', '.join(tags_built)),
                fg='green')

    ctx.invoke(images)


def no_dockerfiles_already_exist(base_images):
    for base_image in base_images:
        filename = get_filename_from_base_image(base_image, base_images)
        if os.path.exists(filename):
            return False

    return True


@pydockerize.command()
@click.pass_context
def images(ctx):
    """Show images for repo from --tag"""

    tag = ctx.obj['tag']

    if tag:
        click.echo('\nShowing Docker images for %s:\n' % tag)
        show_docker_images(tag)


@pydockerize.command()
@click.pass_context
def run(ctx):
    """Run a Docker container"""

    tag = ctx.obj['tag']
    mount_volume_from_host = True

    cmd = get_run_cmd(tag, mount_volume_from_host)

    status = subprocess.call(cmd)


def get_run_cmd(tag, mount_volume_from_host=True):
    cmd = ['docker', 'run']
    cmd.append('-it')
    if mount_volume_from_host:
        cmd.append('-v')
        cmd.append('%s:/host' % os.getcwd())
    cmd.append(tag)
    return cmd


def build_one(tag, base_image, base_images, filename):
    cmd = ['docker', 'build']
    if tag:
        if ':' in tag:
            raise Exception("':' in tag not supported yet")
        tag = tag + ':' + get_tag_from_base_image(base_image, base_images)
        cmd.append('--tag')
        cmd.append(tag)
    if filename != 'Dockerfile':
        cmd.append('--file')
        cmd.append(filename)
    cmd.append('.')
    click.echo("build_one: Calling subprocess with cmd = '%s'\n"
               % ' '.join(cmd))
    status = subprocess.call(cmd)
    if status == 0:
        click.secho('build_one: Docker build for tag "%s" succeeded.' % tag,
                    fg='green')
        return tag
    else:
        click.secho('build_one: Docker build for tag "%s" failed with %d'
                    % (tag, status),
                    fg='red')
        raise click.Abort()


def show_docker_images(repo):
    cmd = ['docker', 'images', repo]
    return subprocess.call(cmd)


def get_filename_from_base_image(base_image, base_images):
    if len(base_images) == 1:
        return 'Dockerfile'
    else:
        return 'Dockerfile-' + base_image


def get_tag_from_base_image(base_image, base_images):
    if len(base_images) == 1:
        return 'latest'

    tag = base_image
    replacements = {'python:': 'py', '-onbuild': ''}

    for old, new in replacements.items():
        tag = tag.replace(old, new)

    return tag


if __name__ == '__main__':
    pydockerize()
