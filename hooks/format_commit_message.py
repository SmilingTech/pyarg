"""
This script is a custom hook for pre-commit that checks if the commit message follows the expected
format. Then, it formats the commit message to match the project conventions.
"""

import re
import sys
from enum import Enum
from pathlib import Path

from conventional_pre_commit.format import ConventionalCommit


# Enums.
class CommitTypeEmoji(Enum):
    """
    Emoji representations for different commit types.
    """

    FEAT = "🔥"
    FIX = "🐛"
    DOCS = "📝"
    STYLE = "💄"
    REFACTOR = "✨"
    TEST = "🔍"
    CHORE = "⚙️"
    REVERT = "⏪"
    CI = "🚀"
    BUILD = "🚧"
    PERF = "⚡️"

    @classmethod
    def types(cls) -> list[str]:
        """
        Get the list of available commit types.

        Returns:
            list[str]: A list of commit types.
        """
        return [name.lower() for name in cls.__members__]


# Functions.
def main(log: bool = True) -> None:
    """
    Entry point for the script.

    Args:
        log (bool): Whether to log the results to the console. Defaults to True.
    """

    # Utils.
    def logger(message: str) -> None:
        print(message) if log else None

    def capitalize_after_final_dot(match: re.Match[str]) -> str:
        match_str: str = match.group(0)
        return match_str.capitalize()

    # Get the commit message from arguments.
    try:
        commit_msg_filepath = sys.argv[1]
        commit_message = Path(commit_msg_filepath).read_text(encoding="utf-8").strip()
    except Exception as e:
        logger("Unable to read the commit message file. " + str(e))
        sys.exit(1)

    # Get commit type.
    conventional_commit_pattern = ConventionalCommit().r_types
    commit_type_re = re.compile(pattern=conventional_commit_pattern)
    commit_type_match = commit_type_re.search(string=commit_message)
    if not commit_type_match:
        logger("Could not parse commit type from message.")
        sys.exit(1)
    commit_type: str = commit_type_match.group(0)

    # Get main commit message.
    main_message_pattern = ConventionalCommit().r_subject
    main_message_re = re.compile(pattern=main_message_pattern)
    main_message_match = main_message_re.search(string=commit_message)
    if not main_message_match:
        logger("Could not parse main commit message from message.")
        sys.exit(1)
    main_commit_message: str = main_message_match.group(0).strip()

    # Capitalize the first letter of the commit description and
    # after any final dot.
    new_main_commit_message = main_commit_message[0].upper() + main_commit_message[1:]
    capitalize_after_final_dot_re = re.compile(pattern=r"(?<=\.\s)(\w)")
    new_main_commit_message_str = capitalize_after_final_dot_re.sub(
        repl=capitalize_after_final_dot, string=new_main_commit_message
    )

    # Add only one final dot at the end of the commit description if it doesn't already have one.
    final_dot_re = re.compile(pattern=r"(?<![!?])\.*$")
    new_main_commit_message_str = final_dot_re.sub(repl="", string=new_main_commit_message_str)
    new_main_commit_message_str += "."

    # Get emoji for commit message.
    if commit_type not in CommitTypeEmoji.types():
        logger("Could not find emoji for the commit type: " + commit_type)
        sys.exit(1)
    commit_type_emoji = CommitTypeEmoji[commit_type.upper()].value

    # Format final commit message.
    formatted_commit_message = f"{commit_type_emoji} {commit_message}"
    formatted_commit_message = formatted_commit_message.replace(main_commit_message, new_main_commit_message_str, 1)

    # Write the formatted commit message back to the file.
    Path(commit_msg_filepath).write_text(formatted_commit_message, encoding="utf-8")


if __name__ == "__main__":
    main()
