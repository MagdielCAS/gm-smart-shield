import time
from typing import Dict, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from gm_shield.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests_per_minute = getattr(settings, "RATELIMIT_DEFAULT", 100)
        # Dictionary to store request counts: {ip: (count, window_start_time)}
        self.request_counts: Dict[str, Tuple[int, float]] = {}
        self.last_cleanup = time.time()
        self.cleanup_interval = 60  # Check every minute
        self.max_entries = 10000  # Maximum number of IP entries to track

    async def dispatch(self, request: Request, call_next) -> Response:
        current_time = time.time()

        # Periodic cleanup of old entries to prevent memory leak
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time

        client_ip = request.client.host if request.client else "unknown"

        if client_ip not in self.request_counts:
            # If we've reached the maximum number of tracked IPs,
            # we might be under a rotation attack.
            # In this case, we'll do an emergency cleanup.
            if len(self.request_counts) >= self.max_entries:
                self._cleanup_old_entries(current_time)
                # If still full, we must reject or allow (reject is safer for DoS)
                if len(self.request_counts) >= self.max_entries:
                     return JSONResponse(
                        status_code=429,
                        content={"detail": "Server under heavy load. Please try again later."}
                    )
            self.request_counts[client_ip] = (1, current_time)
        else:
            count, window_start = self.request_counts[client_ip]
            if current_time - window_start < 60:
                if count >= self.requests_per_minute:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded. Please try again later."}
                    )
                self.request_counts[client_ip] = (count + 1, window_start)
            else:
                # Reset window
                self.request_counts[client_ip] = (1, current_time)

        response = await call_next(request)
        return response

    def _cleanup_old_entries(self, current_time: float):
        """Remove entries that are older than their 60-second window."""
        expired_ips = [
            ip for ip, (_, window_start) in self.request_counts.items()
            if current_time - window_start > 60
        ]
        for ip in expired_ips:
            del self.request_counts[ip]
