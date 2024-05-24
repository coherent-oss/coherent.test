import os
import runpy
import sys

import pip_run
from coherent.build import bootstrap


def run():
    os.environ.update(
        PYTEST_ADDOPTS='--import-mode importlib',
    )
    with bootstrap.write_pyproject(), pip_run.deps.load('.[test]') as home:
        sys.path.insert(0, str(home))
        runpy.run_module('pytest', run_name='__main__')


__name__ == '__main__' and run()
