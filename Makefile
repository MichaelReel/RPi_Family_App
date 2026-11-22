.PHONY: setup lint format typecheck test run demo-clock demo-met demo-icons check clean

setup:
	uv sync

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy lib main.py config.py demos/clock_demo.py demos/met_demo.py demos/icons_demo.py test

test:
	QT_QPA_PLATFORM=offscreen uv run pytest test/

run:
	uv run main.py

demo-clock:
	uv run python demos/clock_demo.py

demo-met:
	uv run python demos/met_demo.py

demo-icons:
	uv run python demos/icons_demo.py

check: lint typecheck test

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -not -path ./.venv -exec rm -rf {} +
