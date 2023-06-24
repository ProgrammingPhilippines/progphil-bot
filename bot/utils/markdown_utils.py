def heading(text: str, level: int):
    string = "#"
    repeated_string = string * level

    return f"{repeated_string} {text}"


def check_box(text: str, checked=False):
    condition = "[x]" if checked is True else "[ ]"
    return f"- {condition} {text}"


def bulleted_items(items):
    return "\n".join([f"- {text}" for text in items])


def code_block_with_style(text: str, language: str):
    return f"```{language}\n{text}\n```"


def code_block(text: str):
    return f"```\n{text}\n```"


def inline_code(text: str):
    return f"`{text}`"


def quote(text: str):
    return f"> {text}"


def block_quote(text: str):
    return f">>> {text}"


def hide_link_embed(url: str):
    return f"<{url}>"


def hyperlink(content: str, url: str):
    return f"[{content}]({url})"
