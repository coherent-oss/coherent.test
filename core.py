import contextlib
import os
import pathlib
import subprocess
import sys
import urllib.request

import pip_run.deps
import pip_run.launch
from coherent.build import bootstrap


def build_env(target, *, orig=os.environ):
    """
    Prepare the environment for invoking pytest.

    Updates the environment with target on PYTHONPATH and
    sets any system-level options.

    >>> env = build_env('foo', orig=dict(PYTHONPATH='bar'))
    >>> env['PYTHONPATH'].replace(os.pathsep, ':')
    'foo:bar'
    """
    overlay = dict(
        PYTHONPATH=pip_run.launch._path_insert(
            orig.get('PYTHONPATH', ''), os.fspath(target)
        ),
        PYTEST_ADDOPTS='--doctest-modules',
        PYTHONSAFEPATH='1',
    )
    return {**orig, **overlay}


def load_ruff_toml():
    url = 'https://raw.githubusercontent.com/jaraco/skeleton/refs/heads/main/ruff.toml'
    return urllib.request.urlopen(url).read().decode('utf-8')


def configure_ruff():
    """
    >>> getfixture('monkeypatch').chdir(getfixture('tmp_path'))
    >>> with configure_ruff():
    ...     pathlib.Path('ruff.toml').stat().st_size > 0
    True
    """
    if pathlib.Path('(meta)/ruff.toml').exists():
        raise NotImplementedError
    return bootstrap.assured(pathlib.Path('ruff.toml'), load_ruff_toml)


@contextlib.contextmanager
def project_on_path():
    """
    Install the project under test and yield its new install path.
    """
    deps = pip_run.deps.load('--editable', '.[test]')
    with bootstrap.write_pyproject(), deps as home, configure_ruff():
        yield home


def run():
    with project_on_path() as home:
        cmd = [sys.executable, '-m', 'pytest', *sys.argv[1:]]
        proc = subprocess.Popen(cmd, env=build_env(home))
        raise SystemExit(proc.wait())
