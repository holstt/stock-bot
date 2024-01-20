import logging
import time

from src import service, utils

utils.setup_logging(logging.INFO)

PLOT_TICKER = "AAPL"

# result = service.get_5d_summary("AAPL")
result = service.get_chart_message(PLOT_TICKER)
test_data_dir = "./tests/test_data"
plot_file_path = f"{test_data_dir}/plot{time.time()}.png"
result.buffer.seek(0)  # type: ignore
with open(plot_file_path, "wb") as f:
    f.write(result.buffer.read())  # type: ignore


print("Done")
