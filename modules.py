import sys


def restore(saved=dict(sys.modules)):
    """
    Save and restore sys.modules.

    Ref coherent-oss/coherent.test#3
    """
    sys.modules.clear()
    sys.modules.update(saved)
