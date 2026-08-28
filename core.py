import contextlib
import functools
import importlib.metadata
import os
import pathlib
import subprocess
import sys
import urllib.request

# Honor PYTHONSAFEPATH on Python 3.10 (a no-op there) before importing
# pip_run et al., so a cwd module can't shadow a stdlib import. Must sort
# ahead of pip_run/coherent.build; see coherent-oss/system (3.10 shadow).
import jaraco.compat.py310.safe_path
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


def pytest_command(*args):
    """
    Build the command to run pytest with a safe path.

    On 3.11+, PYTHONSAFEPATH (set by build_env) keeps the cwd off sys.path.
    Python 3.10 ignores PYTHONSAFEPATH, and isolated mode (-I) would also
    drop PYTHONPATH (which build_env relies on), so instead strip the cwd
    in-process — via the compat shim's import side effect — before importing
    pytest, so a cwd module can't shadow a stdlib import.
    """
    if sys.version_info >= (3, 11):
        return [sys.executable, '-m', 'pytest', *args]
    bootstrap = (
        'import jaraco.compat.py310.safe_path, sys;'
        ' from pytest import console_main; sys.exit(console_main())'
    )
    return [sys.executable, '-c', bootstrap, *args]


def run():
    with project_on_path() as home:
        emit_installed_packages(None)
        proc = subprocess.Popen(pytest_command(*sys.argv[1:]), env=build_env(home))
        raise SystemExit(proc.wait())
