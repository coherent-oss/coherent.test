import contextlib
import functools
import importlib.metadata
import os
import pathlib
import subprocess
import sys
import urllib.request

import jaraco.functools
import pip_run.deps  # type: ignore[import-untyped]
import pip_run.launch  # type: ignore[import-untyped]
from coherent.build import bootstrap  # type: ignore[import-untyped]


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


def load_skeleton_file(name):
    url = f'https://raw.githubusercontent.com/jaraco/skeleton/refs/heads/main/{name}'
    return urllib.request.urlopen(url).read().decode('utf-8')


def configure(name):
    """
    >>> getfixture('monkeypatch').chdir(getfixture('tmp_path'))
    >>> with configure('ruff.toml'):
    ...     pathlib.Path('ruff.toml').stat().st_size > 0
    True
    """
    if pathlib.Path(f'(meta)/{name}').exists():
        # for future, consider honoring this file
        raise NotImplementedError
    return bootstrap.assured(
        pathlib.Path(name),
        functools.partial(load_skeleton_file, name),
    )


@contextlib.contextmanager
def project_on_path():
    """
    Install the project under test and yield its new install path.
    """
    deps = pip_run.deps.load('--editable', '.[test]')
    with (
        bootstrap.write_pyproject(),
        deps as home,
        configure('ruff.toml'),
        configure('mypy.ini'),
    ):
        yield home


@jaraco.functools.bypass_unless(functools.partial(os.environ.get, 'CI'))
def emit_installed_packages(_=None):
    """
    When running in CI, emit the installed packages in a pip-compatible format.

    Uses importlib.metadata rather than shelling out to pip, so it works
    in environments that supply no pip (e.g. a uv-provisioned env under
    ``uvx``). See coherent-oss/coherent.test#26.

    >>> getfixture('monkeypatch').delenv('CI', raising=False)
    >>> emit_installed_packages(None)
    >>> getfixture('monkeypatch').setenv('CI', '1')
    >>> emit_installed_packages(None)  # doctest: +ELLIPSIS
    installed: ...
    """
    packages = ' '.join(
        sorted(
            f'{dist.name}=={dist.version}'
            for dist in importlib.metadata.distributions()
        )
    )
    print('installed:', packages)


def run():
    with project_on_path() as home:
        emit_installed_packages(None)
        cmd = [sys.executable, '-m', 'pytest', *sys.argv[1:]]
        proc = subprocess.Popen(cmd, env=build_env(home))
        raise SystemExit(proc.wait())
