"""FastAPI REST API for transactions - in-memory implementation.

Entry point: creates the FastAPI app, wires up rate limiting and error
handling, and mounts the route modules. Run with:

    uvicorn src.app:app --reload

or directly:

    python src/app.py
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from src.models.transaction import ErrorResponse
from src.routes.accounts import router as accounts_router
from src.routes.transactions import router as transactions_router
from src.utils.rate_limiter import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS, rate_limiter

app = FastAPI(
    title="Transactions API",
    description="Basic in-memory REST API for managing financial transactions.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
# Basic fixed-window limiter: max 100 requests per minute per client IP.
# Applies to every request, before routing. See src/utils/rate_limiter.py for
# the limitations of this in-memory approach.

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining, retry_after = rate_limiter.check(client_ip)

    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Too Many Requests",
                "details": [{
                    "field": "general",
                    "message": (
                        f"Rate limit exceeded: max {RATE_LIMIT_MAX_REQUESTS} requests "
                        f"per {int(RATE_LIMIT_WINDOW_SECONDS)} seconds. Try again later."
                    ),
                }],
            },
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
# FastAPI/Pydantic raise 422 for validation errors by default; the spec asks
# for 400 on bad input with a structured {"error", "details": [...]} body, so
# `RequestValidationError` (covers bad request bodies, query params, and any
# `ValueError` raised inside a Pydantic field/model validator) is normalized
# into that shape here.
#
# There is deliberately no generic `except ValueError` handler: every
# `ValueError` this app raises today lives inside a Pydantic validator
# (see src/validators/transaction_validator.py and
# src/models/transaction.py), which Pydantic/FastAPI already convert into a
# `RequestValidationError` before it ever reaches route code. A catch-all
# `ValueError` -> 400 handler would instead risk masking a genuine server
# bug (e.g. a stray `ValueError` from unrelated code) as an innocuous client
# error, and would leak raw internal exception text to callers.

_VALUE_ERROR_PREFIX = "Value error, "

_LOC_PREFIXES_TO_DROP = {"body", "query", "path", "header", "cookie"}


def _field_name_from_loc(loc: tuple) -> str:
    parts = [str(p) for p in loc if p not in _LOC_PREFIXES_TO_DROP]
    return ".".join(parts) if parts else "general"


def _clean_message(msg: str) -> str:
    # Pydantic v2 prefixes messages raised via `raise ValueError(...)` in
    # custom validators with "Value error, " - strip that for a clean message.
    if msg.startswith(_VALUE_ERROR_PREFIX):
        return msg[len(_VALUE_ERROR_PREFIX):]
    return msg


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": _field_name_from_loc(err["loc"]), "message": _clean_message(err["msg"])}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Validation failed", "details": details},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # Some routes raise HTTPException with a structured dict detail (already
    # in the {"error", "details"} shape); others just pass a plain string.
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = ErrorResponse(error=exc.detail).model_dump()
    return JSONResponse(status_code=exc.status_code, content=content)


# ---------------------------------------------------------------------------
# OpenAPI schema
# ---------------------------------------------------------------------------
# FastAPI auto-generates a default "422 Validation Error" response for every
# route that takes a body/query/path parameter. Since the exception handler
# above rewrites those failures to 400 at runtime, the generated schema would
# otherwise document a status code the API never actually returns. Patch the
# schema after generation so it advertises 400 (matching runtime behavior)
# instead of the framework default of 422.

def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            responses = operation.get("responses")
            if not responses or "422" not in responses:
                continue
            legacy_422 = responses.pop("422")
            # Most routes already document their own accurate 400 (see the
            # `responses=` kwargs in src/routes/*.py) - don't clobber that
            # with the generic auto-422 schema. Only synthesize a 400 entry
            # from the framework default where nothing better was declared.
            if "400" not in responses:
                legacy_422["description"] = "Validation failed"
                responses["400"] = legacy_422

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(transactions_router)
app.include_router(accounts_router)


@app.get("/")
def root() -> dict:
    return {"service": "Transactions API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
