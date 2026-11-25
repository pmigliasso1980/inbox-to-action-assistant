"""Schedule a reminder from the queue's wire format."""

def schedule(packet: dict[str, int], now_epoch_seconds: int) -> dict[str, int]:
    delay = packet["delay_seconds"]
    if type(delay) is not int or delay < 0:
        raise ValueError("delay_seconds must be a nonnegative integer")
    return {"due_at_epoch_seconds": now_epoch_seconds + delay}
