"""Plugin initialization script"""

try:
    from pycharmdebug.menu import install  # type: ignore

    install()
except ImportError:
    pass
