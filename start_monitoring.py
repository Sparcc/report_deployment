import getpass
from report_deployment import *

env = Environment(getpass.getpass('Hipchat password:'))
beginMonitoring(env)