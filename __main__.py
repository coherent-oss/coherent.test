import contextlib
import os
import runpy
import sys

from . import modules

import pip_run
from coherent.build import bootstrap


@contextlib.contextmanager
def project_on_path():
    """
    Install the project under test to sys.path.
    """
    deps = pip_run.deps.load('--editable', '.[test]')
    with bootstrap.write_pyproject(), deps as home:
        sys.path.insert(0, str(home))
        yield


def run():
    os.environ.update(
        PYTEST_ADDOPTS='--doctest-modules',
    )
    with project_on_path():
        modules.restore()
        runpy.run_module('pytest', run_name='__main__')


__name__ == '__main__' and run()
