import importlib.util
import json
import shutil


result = {
    'websocket_client_available': importlib.util.find_spec('websocket')
    is not None,
    'chrome': (
        shutil.which('google-chrome')
        or shutil.which('google-chrome-stable')
        or shutil.which('chromium')
        or shutil.which('chromium-browser')
    ),
}
print(json.dumps(result, sort_keys=True))
assert result == {'websocket_client_available': False, 'chrome': None}
