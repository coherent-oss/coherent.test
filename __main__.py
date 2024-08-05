import contextlib
import os
import subprocess
import sys

import pip_run.deps
import pip_run.launch
from coherent.build import bootstrap


def build_env(target, *, orig=os.environ):
    """
    Update environment with target on PYTHONPATH.
    """
    overlay = dict(
        PYTHONPATH=pip_run.launch._path_insert(
            orig.get('PYTHONPATH', ''), os.fspath(target)
        ),
    )
    return {**orig, **overlay}


@contextlib.contextmanager
def project_on_path():
    """
    Install the project under test and yield its new install path.
    """
    deps = pip_run.deps.load('--editable', '.[test]')
    with bootstrap.write_pyproject(), deps as home:
        yield home


def run():
    os.environ.update(
        PYTEST_ADDOPTS='--doctest-modules',
    )
    with project_on_path() as home:
        cmd = [sys.executable, '-m', 'pytest', *sys.argv[1:]]
        proc = subprocess.Popen(cmd, env=build_env(home))
        raise SystemExit(proc.wait())


__name__ == '__main__' and run()
