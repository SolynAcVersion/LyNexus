import sys
sys.path.insert(0, '.')

try:
    from api_server import app
    print("✓ Successfully imported api_server.app")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    import traceback
    traceback.print_exc()
