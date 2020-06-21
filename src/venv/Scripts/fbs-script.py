#!"c:\users\paul disbeschl\documents\new folder (2)\src\venv\scripts\python.exe"
# EASY-INSTALL-ENTRY-SCRIPT: 'fbs==0.8.6','console_scripts','fbs'
__requires__ = 'fbs==0.8.6'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('fbs==0.8.6', 'console_scripts', 'fbs')()
    )
