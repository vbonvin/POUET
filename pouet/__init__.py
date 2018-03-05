__all__ = ["config", "obsprogram", "clouds", "design", "main", "meteo", "obs", "plots", "run", "util"]


# add the pouet package to sys path so submodules can be called directly
# todo: find a way to use absolute imports instead, i.e. pouet.obs instead of obs

import os, sys
path = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])))
sys.path.append(path)

