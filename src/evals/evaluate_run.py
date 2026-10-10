"""Run the Ragas evaluator implemented in the repository's main module.

This compatibility entry point intentionally delegates to ``main.py`` so there
is one evaluation implementation and no separate hard-coded score path.
"""

from main import main as _evaluation_main


if __name__ == "__main__":
    _evaluation_main()
