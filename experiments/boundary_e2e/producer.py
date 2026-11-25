"""Convert an inbox review reminder into the queue's wire format."""

def encode_reminder(delay_minutes: int) -> dict[str, int]:
    if type(delay_minutes) is not int or delay_minutes < 0:
        raise ValueError("delay_minutes must be a nonnegative integer")
    # Intentional lab defect: the wire field requires seconds.
    return {"delay_seconds": delay_minutes}
