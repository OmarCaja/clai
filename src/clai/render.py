from types import TracebackType
from typing import Self

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown


class MarkdownStream:
    """Shows streamed text as Markdown, redrawing it as chunks arrive.

    Markdown can't be rendered chunk by chunk (a `**` means nothing until its
    closing `**` arrives), so the whole text so far is re-rendered on each write.
    """

    def __init__(self, console: Console) -> None:
        self._console = console
        self._live: Live | None = None
        self._text = ""

    def write(self, chunk: str) -> None:
        """Add a chunk, starting a new block if the previous one was closed."""
        live = self._live if self._live is not None else self._start_block()
        self._text += chunk
        live.update(Markdown(self._text), refresh=True)

    def _start_block(self) -> Live:
        live = Live(console=self._console, auto_refresh=False)
        live.start()
        self._live = live
        self._text = ""
        return live

    def close(self) -> None:
        """Freeze what is shown, so other output can be printed below it."""
        if self._live is not None:
            self._live.stop()
            self._live = None

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
