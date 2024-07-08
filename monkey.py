from __future__ import annotations

import functools
import importlib
import pathlib
from typing import TYPE_CHECKING

from coherent.build import discovery

if TYPE_CHECKING:
    from _typeshed import StrPath
    from types import ModuleType

best_name = functools.lru_cache(maxsize=None)(discovery.best_name)


def import_path(
    path: StrPath, *, root: pathlib.Path, **unused_kwargs
) -> ModuleType:
    """
    Import the given path relative to the root.

    Overrides _pytest.pathlib.import_path to honor the essential layout.
    """
    rel_path = pathlib.Path(path).relative_to(root).with_suffix('')
    rel_name = '.'.join(rel_path.parts)
    module_name = f"{best_name()}.{rel_name}"
    if module_name.endswith(init_module := ".__init__"):
        module_name = module_name[:-len(init_module)]
    return importlib.import_module(module_name)


def patch_all():
    import _pytest.config
    import _pytest.python

    _pytest.config.import_path = import_path
    _pytest.python.import_path = import_path


def pytest_configure():
    patch_all()
