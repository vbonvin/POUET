__all__ = ["config", "obsprogram", "clouds", "design", "main", "meteo", "obs", "plots", "run", "util"]


# add the pouet package to sys path so submodules can be called directly
# todo: find a way to use absolute imports instead, i.e. pouet.obs instead of obs

import os, sys, inspect
path = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
sys.path.append(path)

