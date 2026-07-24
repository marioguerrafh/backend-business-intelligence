#!/usr/bin/env python3
"""Test synchronization endpoints."""
import sys
sys.path.insert(0, '/app')

import urllib.request
import json

def test_endpoint(url, method='GET'):
    """Test an endpoint."""
    try:
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return response.status, data
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return None, str(e)

print("=" * 60)
print("TESTANDO ENDPOINTS DE SINCRONIZAÇÃO")
print("=" * 60)

# Test health
print("\n1. GET /v1/synchronization/health")
status, data = test_endpoint('http://localhost:8000/v1/synchronization/health')
print(f"   Status: {status}")
print(f"   Response: {json.dumps(data, indent=2)}")

# Test scheduler status
print("\n2. GET /v1/synchronization/scheduler/status")
status, data = test_endpoint('http://localhost:8000/v1/synchronization/scheduler/status')
print(f"   Status: {status}")
print(f"   Response: {json.dumps(data, indent=2)}")

# Test jobs list
print("\n3. GET /v1/synchronization/jobs")
status, data = test_endpoint('http://localhost:8000/v1/synchronization/jobs')
print(f"   Status: {status}")
print(f"   Response: {json.dumps(data, indent=2)}")

# Test runtime metrics
print("\n4. GET /v1/synchronization/runtime")
status, data = test_endpoint('http://localhost:8000/v1/synchronization/runtime')
print(f"   Status: {status}")
print(f"   Response: {json.dumps(data, indent=2)}")

print("\n" + "=" * 60)
print("✅ TODOS OS ENDPOINTS TESTADOS!")
print("=" * 60)
print("\nPróximos passos:")
print("  1. Abrir http://localhost:8000/docs")
print("  2. Iniciar scheduler: POST /v1/synchronization/scheduler/start")
print("  3. Agendar sincronização de teste")
print("=" * 60)
