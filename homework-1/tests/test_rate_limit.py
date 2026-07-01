from src.utils.rate_limiter import RATE_LIMIT_MAX_REQUESTS


def test_requests_under_limit_succeed_and_report_remaining(client):
    resp = None
    for _ in range(10):
        resp = client.get("/")
        assert resp.status_code == 200

    assert resp.headers["X-RateLimit-Limit"] == str(RATE_LIMIT_MAX_REQUESTS)
    assert int(resp.headers["X-RateLimit-Remaining"]) == RATE_LIMIT_MAX_REQUESTS - 10


def test_requests_at_exactly_the_limit_all_succeed(client):
    for _ in range(RATE_LIMIT_MAX_REQUESTS):
        resp = client.get("/")
        assert resp.status_code == 200


def test_request_over_the_limit_returns_429(client):
    for _ in range(RATE_LIMIT_MAX_REQUESTS):
        resp = client.get("/")
        assert resp.status_code == 200

    resp = client.get("/")
    assert resp.status_code == 429
    body = resp.json()
    assert body["error"] == "Too Many Requests"
    assert "Retry-After" in resp.headers


def test_rate_limit_applies_across_different_endpoints(client):
    # The limiter counts all requests from an IP, not per-route.
    for _ in range(RATE_LIMIT_MAX_REQUESTS):
        client.get("/transactions")

    resp = client.get("/transactions")
    assert resp.status_code == 429


def test_rate_limit_state_is_reset_between_tests(client):
    # If the previous tests' counters leaked into this one, even the first
    # request here would be throttled.
    resp = client.get("/")
    assert resp.status_code == 200
