"""JSON-in/JSON-out entry point for the toy inbox reminder feature."""

import json
import sys

from .consumer import schedule
from .producer import encode_reminder


def main() -> None:
    request = json.load(sys.stdin)
    packet = encode_reminder(request["delay_minutes"])
    print(json.dumps(schedule(packet, request["now_epoch_seconds"])))


if __name__ == "__main__":
    main()
