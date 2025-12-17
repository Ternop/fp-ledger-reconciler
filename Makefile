.PHONY: dev test fmt

dev:
	uvicorn app.main:app --reload

test:
	pytest -q

fmt:
	ruff check . --fix
