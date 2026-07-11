requirements:(double check pyproject.toml)


commands:
uvicorn backend.main:app --reload

uv run alembic init -t async alembic 

uv run alembic revision --autogenerate -m "anyname u desire for the action "

uv run alembic upgrade head       ####the opposite of####     uv run alembic downgrade -1

uv run alembic current
