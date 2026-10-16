"""Limit published operations to the canonical API URL space."""


def canonical_api_endpoints(endpoints):
    return [
        endpoint for endpoint in endpoints
        if endpoint[0].startswith('/api/')
        and endpoint[0] not in ('/api/schema/', '/api/docs/')
    ]
