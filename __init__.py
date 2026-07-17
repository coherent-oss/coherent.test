"""
A trivial doctest to cause something to be tested.

>>> __name__
'coherent.test'
"""

__license__ = 'Apache-2.0'

__requires__ = [
    'pytest',
    'pytest-enabler',
    'pytest-ruff',
    # Exclude PyPy from type checks (python/mypy#20454 jaraco/skeleton#187)
    # disabled for coherent-oss/coherent.test#23
    # "pytest-mypy; platform_python_implementation != 'PyPy'",
]
