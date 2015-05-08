import hipstatus
import logging
from preferences import user_info
import sys

home = user_info()[1]

# Pass any value as the first parameter to the main script to run with DEBUG log output
try:
    sys.argv[1]
except IndexError:
    level = logging.INFO
else:
    level = logging.DEBUG

logging.basicConfig(filename='{}/Library/Logs/HipStatus.log'.format(home),
                    format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m-%d-%Y %I:%M:%S %p',
                    level=level)

logging.info("Starting HipStatus...")

HipStatus = hipstatus.App()
HipStatus.run()