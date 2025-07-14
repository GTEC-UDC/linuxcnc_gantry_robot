from pygments.lexer import RegexLexer
from pygments.token import (
    Text,
    Comment,
    Keyword,
    Name,
    String,
    Number,
    Operator,
    Punctuation,
)


class HALLexer(RegexLexer):
    """
    A Pygments lexer for LinuxCNC HAL files.
    """

    name = "HAL"
    aliases = ["hal"]
    filenames = ["*.hal"]

    tokens = {
        "root": [
            (r"#.*$", Comment),  # Comments start with #
            (
                r"\b(loadrt|addf|setp|net|link|unlink|newinst|loadusr|"
                r"unload|names|personality)\b",
                Keyword,
            ),  # HAL commands
            (r"\b(true|false)\b", Keyword.Constant),  # Booleans `true` and `false`
            (
                r"[a-zA-Z_][a-zA-Z0-9_.-]*",
                Name.Variable,
            ),  # Signal or variable names with dots and dashes
            (r'"[^"]*"', String),  # Strings enclosed in double quotes
            (r"0x[0-9a-fA-F]+", Number.Hex),  # Hexadecimal numbers (e.g., 0x205)
            (r"[+-]?\d+\.\d+", Number.Float),  # Floating-point numbers
            (r"[+-]?\d+", Number.Integer),  # Integers
            (r"[=|&<>]", Operator),  # Operators
            (r"-", Operator),  # Hyphens as operators or part of numbers
            (r"[\[\](),]", Punctuation),  # Brackets, parentheses, commas
            (r"\.", Punctuation),  # Dots
            (r"\s+", Text),  # Whitespace
        ],
    }
