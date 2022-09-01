import os
import sys

frozen = getattr(sys, 'frozen', False)

if frozen:
    # we are running in a bundle
    bundle_dir = sys._MEIPASS + '/'
else:
    # we are running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__)) + '/../'
