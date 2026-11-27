# Run `just` with no arguments to list these.
default:
    @just --list

# Run the test suite. The global pre-push hook looks for this recipe by name.
test:
    uv run pytest

# Fast lint. The global pre-commit hook looks for this recipe by name.
lint:
    uv run ruff check .

# Generate the mesostic from the corpus.
run:
    uv run python mesostics.py

# Compare our spine against Cage's published text.
compare:
    uv run python cage.py

# Every measurement behind FINDINGS.md.
analyse:
    uv run python analysis.py
