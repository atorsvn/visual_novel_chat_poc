from visual_novel_chat.text_utils import paginate_text, wrap_text


def test_wrap_text_limits_line_length():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    wrapped = wrap_text(text, width=10)
    assert all(len(line) <= 10 for line in wrapped.splitlines())


def test_paginate_text_splits_on_line_count():
    text = "\n".join(str(i) for i in range(7))
    pages = paginate_text(text, lines_per_page=3)
    assert pages == ["0\n1\n2", "3\n4\n5", "6"]


def test_paginate_text_empty_string_returns_single_page():
    assert paginate_text("", lines_per_page=3) == [""]
