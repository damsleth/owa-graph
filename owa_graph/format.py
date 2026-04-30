"""Pretty-printers for common Graph response shapes.

Graph paginates collections under `value`, with `@odata.nextLink` for
continuation. We surface a small handful of well-known shapes (users,
groups, messages, drive items) as compact tables; everything else falls
through to indented JSON so `--pretty` is always at least a little
nicer than the default single-line output.
"""
import json


def _pad(s, width):
    s = str(s) if s is not None else ''
    if len(s) >= width:
        return s
    return s + ' ' * (width - len(s))


def _looks_like_users(items):
    return all(isinstance(i, dict) and ('displayName' in i or 'userPrincipalName' in i) for i in items)


def _looks_like_messages(items):
    return all(
        isinstance(i, dict) and 'subject' in i and ('from' in i or 'sender' in i)
        for i in items
    )


def _looks_like_drive_items(items):
    return all(isinstance(i, dict) and 'name' in i and ('size' in i or 'folder' in i or 'file' in i) for i in items)


def _format_users(items):
    rows = [(i.get('displayName') or '',
             i.get('userPrincipalName') or i.get('mail') or '',
             i.get('id') or '') for i in items]
    if not rows:
        return '(no items)'
    name_w = max(len(r[0]) for r in rows)
    upn_w = max(len(r[1]) for r in rows)
    return '\n'.join(
        f'{_pad(n, name_w)}  {_pad(u, upn_w)}  {i}' for n, u, i in rows
    )


def _format_messages(items):
    rows = []
    for m in items:
        sender = m.get('from') or m.get('sender') or {}
        addr = (sender.get('emailAddress') or {}).get('address') or ''
        rows.append((
            m.get('receivedDateTime', '')[:16].replace('T', ' '),
            addr,
            m.get('subject') or '',
        ))
    if not rows:
        return '(no items)'
    date_w = max(len(r[0]) for r in rows)
    addr_w = min(max((len(r[1]) for r in rows), default=0), 32)
    return '\n'.join(
        f'{_pad(d, date_w)}  {_pad(a[:addr_w], addr_w)}  {s}'
        for d, a, s in rows
    )


def _format_drive_items(items):
    rows = [(
        'd' if i.get('folder') else 'f',
        str(i.get('size') or ''),
        i.get('name') or '',
    ) for i in items]
    size_w = max(len(r[1]) for r in rows) if rows else 0
    return '\n'.join(
        f'{t}  {_pad(sz, size_w)}  {n}' for t, sz, n in rows
    ) or '(no items)'


def format_pretty(payload):
    """Best-effort pretty printer.

    Recognises Graph-style collection responses (`{value: [...]}`) for a
    few common shapes; otherwise indents the JSON. Always returns a
    string ready for `print()`."""
    if isinstance(payload, dict) and isinstance(payload.get('value'), list):
        items = payload['value']
        if items:
            if _looks_like_users(items):
                return _format_users(items)
            if _looks_like_messages(items):
                return _format_messages(items)
            if _looks_like_drive_items(items):
                return _format_drive_items(items)
    if isinstance(payload, (dict, list)):
        return json.dumps(payload, indent=2, ensure_ascii=False)
    return str(payload)
