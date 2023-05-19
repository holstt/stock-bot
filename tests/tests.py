import logging

from src import service, utils

utils.setup_logging(logging.DEBUG)

result = service.get_5d_summary("AAPL")


print("Done")
