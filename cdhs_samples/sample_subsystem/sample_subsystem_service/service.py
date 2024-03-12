#!/usr/bin/env python3

"""
Boilerplate service code which reads the config file and starts up the
GraphQL/HTTP endpoint. (should not need too much modification)
"""

__author__ = "aussp"
__version__ = "0.1.0"

import logging

from service import schema
from kubos_service.config import Config
from kubos_service import http_service
from logging.handlers import SysLogHandler
import sys

config = Config("sample_subsystem_service")

# Setup logging
logger = logging.getLogger("sample_subsystem_service")
logger.setLevel(logging.DEBUG)
handler = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_DAEMON)
formatter = logging.Formatter('sample_subsystem_service: %(message)s')
handler.formatter = formatter
logger.addHandler(handler)

# Set up a handler for logging to stdout
stdout = logging.StreamHandler(stream=sys.stdout)
stdout.setFormatter(formatter)
logger.addHandler(stdout)

# Start an http service
http_service.start(config, schema.schema)
# TODO: Kill thread if process crashes?
