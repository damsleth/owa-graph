"""HTTP helper for Microsoft Graph (and any other API behind an AAD
audience).

`api_request` returns parsed JSON or None for return-to-caller failures.
For auth/permission failures we exit the process with a clear message -
owa-graph is a CLI, not a library, and there is no recovery path for a
401 except telling the user to re-run.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def api_request(method, base, endpoint, access_token, body=None,
                extra_headers=None, debug=False, raw=False):
    """Issue a request against the API at `base`.

    - `base` and `endpoint` are joined with a single slash.
    - `body` is dict-serialised to JSON when non-None; pass a `bytes`
      object to send raw.
    - `extra_headers` is an optional dict of additional headers.
    - Returns parsed JSON on 2xx (or raw bytes if raw=True),
      None on 404/429 (caller decides), and exits on 401/403
      (unrecoverable without reconfig).
    """
    url = f'{base}/{endpoint}' if not endpoint.startswith('http') else endpoint
    if debug:
        print(f'DEBUG: {method} {url}', file=sys.stderr)
        if body is not None and not isinstance(body, (bytes, bytearray)):
            print(f'DEBUG: body: {json.dumps(body)[:500]}', file=sys.stderr)

    data = None
    headers = {'Authorization': f'Bearer {access_token}'}
    if body is not None:
        if isinstance(body, (bytes, bytearray)):
            data = bytes(body)
        else:
            data = json.dumps(body).encode('utf-8')
            headers['Content-Type'] = 'application/json'
    if extra_headers:
        for k, v in extra_headers.items():
            headers[k] = v

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            payload = resp.read()
            if raw:
                return payload
            if not payload:
                return {}
            return json.loads(payload.decode('utf-8', errors='replace'))
    except urllib.error.HTTPError as e:
        code = e.code
        err_body = e.read().decode('utf-8', errors='replace')
        if code == 401:
            print('ERROR: auth expired (401). Run: owa-graph refresh', file=sys.stderr)
            sys.exit(1)
        if code == 403:
            print('ERROR: access denied (403). Check permissions/scopes.', file=sys.stderr)
            if debug:
                print(err_body, file=sys.stderr)
            sys.exit(1)
        if code == 404:
            print('ERROR: not found (404).', file=sys.stderr)
            return None
        if code == 429:
            print('ERROR: rate limited (429). Try again later.', file=sys.stderr)
            return None
        print(f'ERROR: HTTP {code}', file=sys.stderr)
        if debug:
            print(err_body, file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f'ERROR: {e.reason}', file=sys.stderr)
        return None


def api_get(base, endpoint, access_token, extra_headers=None, debug=False, raw=False):
    return api_request('GET', base, endpoint, access_token,
                       extra_headers=extra_headers, debug=debug, raw=raw)


def build_query(params):
    """Build an OData query string. Values are URL-encoded, keys are
    not (they are $-prefixed OData system params)."""
    parts = []
    for k, v in params.items():
        parts.append(f'{k}={urllib.parse.quote(str(v), safe="")}')
    return '&'.join(parts)


def build_url(base, path, query_pairs=None):
    """Join base + path and append a URL-encoded query string.

    `path` may include or omit a leading slash, and may already contain
    its own `?...` query - in which case `query_pairs` are appended with
    `&`. `query_pairs` is an iterable of `(key, value)` tuples; we keep
    it as tuples (not a dict) so the same key can repeat (`$filter` etc.
    only allow one, but the parser shouldn't enforce that here).
    """
    base = base.rstrip('/')
    has_q = '?' in path
    path = path.lstrip('/')
    url = f'{base}/{path}'
    if not query_pairs:
        return url
    encoded = '&'.join(
        f'{k}={urllib.parse.quote(str(v), safe="")}' for k, v in query_pairs
    )
    sep = '&' if has_q else '?'
    return f'{url}{sep}{encoded}'
