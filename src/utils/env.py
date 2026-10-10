"""Load local project configuration with a predictable precedence order."""

from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_project_environment() -> None:
    """Load process env first, then Databricks settings, then general defaults.

    ``override=False`` preserves already-set process variables. Loading the
    Databricks VS Code env file before ``.env`` makes it the source of local
    workspace credentials while allowing ``.env`` to supply missing values.
    """
    load_dotenv(PROJECT_ROOT / ".databricks" / ".databricks.env", override=False)
    load_dotenv(PROJECT_ROOT / ".env", override=False)
