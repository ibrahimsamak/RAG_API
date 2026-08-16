from slowapi import Limiter
from slowapi.util import get_remote_address

# Single shared limiter, imported by main.py (wiring) and the routers (decorators).
# Defaults to in-memory storage — fine for a single instance. Back it with Redis
# via `storage_uri="redis://..."` if you run multiple workers behind a load balancer.
limiter = Limiter(key_func=get_remote_address)
