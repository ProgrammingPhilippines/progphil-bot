def heading(text: str, level: int):
    string = "#"
    repeated_string = string * level

    return f"{repeated_string} {text}"


def check_box(text: str, checked=False):
    ternary = "[x]" if checked is True else "[ ]"
    return f"- {ternary} {text}"


def list_items(items):
    return "\n".join([f"- {text}" for text in items])


def code_block(text: str, code_style: str, highlight=False):
    ternary = f"```{code_style}\n{text} \n```" if highlight is True else f"```\n{text} \n```"
    return f"{ternary}"


def inline_code(text: str):
    return f"`{text}`"
