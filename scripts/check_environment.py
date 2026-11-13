#!/usr/bin/env python3
"""Print runtime and analysis dependency versions."""
import platform, sys
from importlib.metadata import PackageNotFoundError, version

print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.machine()}")
for name in ("Pillow", "numpy", "scipy", "matplotlib", "soundfile"):
    try:
        print(f"{name}: {version(name)}")
    except PackageNotFoundError:
        print(f"{name}: NOT INSTALLED")
