import google.cloud.logging
import logging
import sys

from src.preprocessor.preprocessor import main as preprocessor

client = google.cloud.logging.Client()
client.setup_logging()
# logging.root.setLevel(logging.DEBUG)


def main(command):
    logging.info("Command: %s", command)

    function_map = {
        "preprocess": preprocessor,
    }

    function = function_map.get(command, lambda: None)

    try:
        function()

    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Need sys argument!")

    else:
        main(sys.argv[1])
