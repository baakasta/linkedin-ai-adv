requirements:(double check pyproject.toml)
    fastapi==0.139.0
    uvicorn[standard]==0.50.0
    sqlalchemy==2.0.51
    pydantic==2.13.4
    email-validator==2.3.0

commands:uvicorn backend.main:app --reload


