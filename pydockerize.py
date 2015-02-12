#!/usr/bin/env python

import os
import subprocess
import sys

import click


@click.command()
@click.version_option()
@click.argument('requirements_file', type=click.Path(exists=True))
@click.pass_context
def pydockerize(ctx, requirements_file):
    """Create Docker images for Python apps"""
    print('requirements_file = %r' % requirements_file)
    if not os.path.exists('Dockerfile'):
        write_dockerfile()


def write_dockerfile():
    print('write_dockerfile')


if __name__ == '__main__':
    pydockerize()
