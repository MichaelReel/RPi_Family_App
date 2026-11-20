.PHONY: setup lint format typecheck test run demo-clock demo-met demo-icons check clean

setup:
	uv sync

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy lib main.py config.py demos test

test:
	QT_QPA_PLATFORM=offscreen uv run pytest test/

run:
	uv run main.py

demo-clock:
	uv run python -m demos.clock_demo

demo-met:
	uv run python -m demos.met_demo

demo-icons:
	uv run python -m demos.icons_demo

check: lint typecheck test

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -not -path ./.venv -exec rm -rf {} +
