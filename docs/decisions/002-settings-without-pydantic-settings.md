# 002 - Env-based settings use pydantic + os.environ

Status: accepted

`pydantic-settings` is not in the declared dependency set and the brief limits dependencies.
Settings are a frozen pydantic model populated from `PRICEWATCH_*` environment variables.
