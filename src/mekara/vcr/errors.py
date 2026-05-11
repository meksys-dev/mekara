"""VCR error types."""


class VcrReplayMismatchError(Exception):
    """Raised when VCR replay detects a mismatch between recorded and actual data."""

    def __init__(
        self,
        message: str,
        *,
        show_traceback: bool = True,
        display_error: bool = True,
    ) -> None:
        super().__init__(message)
        self.show_traceback = show_traceback
        self.display_error = display_error
