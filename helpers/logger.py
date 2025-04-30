import ctypes
import re
from datetime import datetime
from os import name as os_name
from typing import Any


class Logger:
    def __init__(self, name: str) -> None:
        self.name = name
        self.name_width = len(self.name)
        if os_name == "nt":
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    ANSI_COLORS = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "gray": "\033[90m",
        "purple": "\033[38;2;128;0;128m",
        "reset": "\033[0m",
        "error": "\033[38;2;255;0;0m",
        "debug": "\033[38;2;128;0;128m",
        "info": "\033[38;2;0;0;255m",
        "warning": "\033[38;2;255;255;0m",
        "success": "\033[38;2;128;0;128m",
        "custom": "\033[38;2;0;255;127m"
    }

    LEVEL_WIDTH = max(len(key) for key in ANSI_COLORS)
    DATE_WIDTH = 8

    @staticmethod
    def convert(color: str) -> str:
        return Logger.ANSI_COLORS.get(color, Logger.ANSI_COLORS["white"])

    @staticmethod
    def colorize(color: str, text: str) -> str:
        return f"{Logger.convert(color)}{text}{Logger.ANSI_COLORS['reset']}"

    @staticmethod
    def strip_ansi(text: str) -> str:
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    @staticmethod
    def pad_with_colors(text: str, width: int, align: str = "left") -> str:
        visible_length = len(Logger.strip_ansi(text))
        padding_needed = max(0, width - visible_length)

        if align == "left":
            return text + " " * padding_needed
        return " " * padding_needed + text

    def log(self, level: str, *args: Any) -> None:
        level = level.lower()

        date = datetime.now().strftime("%H:%M:%S")
        date_colored = Logger.colorize("white", date)
        level_colored = Logger.colorize(level, level.upper())
        name_colored = Logger.colorize("custom", self.name)
        separator = Logger.colorize("gray", "│")

        Logger.pad_with_colors(level_colored, self.LEVEL_WIDTH)
        date_part = Logger.pad_with_colors(date_colored, self.DATE_WIDTH)
        name_part = Logger.pad_with_colors(name_colored, self.name_width)

        message = " ".join(Logger.colorize(level, str(arg)) for arg in args)

        output = f"{date_part} {separator} {name_part} {separator} {message}"  # {level_} {separator}

        print(output)
