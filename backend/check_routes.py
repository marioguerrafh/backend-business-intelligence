#!/usr/bin/env python3
"""Check registered routes in FastAPI app."""

from app.main import app

print("=" * 60)
print("REGISTERED ROUTES IN FASTAPI APP")
print("=" * 60)

all_routes = []
for route in app.routes:
    if hasattr(route, 'path'):
        all_routes.append(route.path)

print(f"\nTotal routes: {len(all_routes)}")
print("\nAll routes:")
for path in sorted(all_routes):
    print(f"  {path}")

sync_routes = [r for r in all_routes if 'synchronization' in r.lower()]
print(f"\nSynchronization routes ({len(sync_routes)}):")
for path in sync_routes:
    print(f"  {path}")

admin_routes = [r for r in all_routes if 'admin' in r.lower()]
print(f"\nAdmin routes ({len(admin_routes)}):")
for path in admin_routes:
    print(f"  {path}")
