"""
Deprecation Middleware for API v1

Adds deprecation headers to all v1 API responses.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime, timedelta
import time


class DeprecationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add deprecation headers to v1 endpoints.
    
    Headers added:
    - Deprecation: true (indicates endpoint is deprecated)
    - Sunset: <date> (when endpoint will be removed)
    - Link: <v2 endpoint>; rel="successor-version" (point to v2)
    - Warning: <message> (deprecation warning message)
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only add deprecation headers to v1 endpoints
        if "/api/v1/" in request.url.path:
            # Calculate sunset date (3 months from now)
            sunset_date = datetime.utcnow() + timedelta(days=90)
            sunset_rfc7231 = sunset_date.strftime("%a, %d %b %Y 23:59:59 GMT")

            # Add deprecation headers
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = sunset_rfc7231

            # Map v1 endpoint to v2 endpoint
            v2_path = request.url.path.replace("/api/v1/", "/api/v2/")
            response.headers["Link"] = f"<{v2_path}>; rel=\"successor-version\""

            # Add warning header
            warning_msg = (
                f'299 - "API v1 is deprecated. '
                f'Will be removed on {sunset_date.strftime("%Y-%m-%d")}. '
                f'Please migrate to /api/v2/ endpoints."'
            )
            response.headers["Warning"] = warning_msg

            # Add deprecation info in response body if response is JSON
            if "application/json" in response.headers.get("content-type", ""):
                response.headers["X-API-Warn"] = (
                    f"v1 endpoints will sunset on {sunset_date.strftime('%Y-%m-%d')}. "
                    f"Migrate to v2: {v2_path}"
                )

        return response
