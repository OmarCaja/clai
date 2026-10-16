from io import StringIO

from rich.console import Console

from clai.render import MarkdownStream


def make_stream() -> tuple[MarkdownStream, StringIO]:
    output = StringIO()
    return MarkdownStream(Console(file=output, width=80)), output


def test_renders_streamed_markdown() -> None:
    stream, output = make_stream()

    with stream:
        for chunk in ["# Ti", "tle\n\n", "- **bo", "ld** item\n"]:
            stream.write(chunk)

    text = output.getvalue()
    assert "Title" in text
    assert "bold item" in text
    assert "#" not in text
    assert "**" not in text


def test_write_after_close_starts_a_new_block() -> None:
    stream, output = make_stream()

    stream.write("first")
    stream.close()
    output.write("$ ls\n")
    stream.write("second")
    stream.close()

    assert output.getvalue().split() == ["first", "$", "ls", "second"]
