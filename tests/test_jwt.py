"""jwt.py is tiny - test the happy path and the failure-tolerant
fallback explicitly so a regression in either is caught."""
import base64
import json
import time

from owa_graph import jwt as jwt_mod


def _make_token(exp_offset_seconds):
    payload = {'exp': int(time.time()) + exp_offset_seconds}
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b'=').decode()
    return f'header.{encoded}.sig'


def test_decode_jwt_segment_round_trip():
    raw = json.dumps({'a': 1, 'b': 'two'}).encode()
    seg = base64.urlsafe_b64encode(raw).rstrip(b'=').decode()
    assert jwt_mod.decode_jwt_segment(seg) == {'a': 1, 'b': 'two'}


def test_token_minutes_remaining_positive():
    tok = _make_token(3600)
    out = jwt_mod.token_minutes_remaining(tok)
    assert out is not None
    assert 58 <= out <= 60


def test_token_minutes_remaining_negative_for_expired():
    tok = _make_token(-3600)
    out = jwt_mod.token_minutes_remaining(tok)
    assert out is not None and out < 0


def test_token_minutes_remaining_handles_garbage():
    assert jwt_mod.token_minutes_remaining('not.a.token') is None
    assert jwt_mod.token_minutes_remaining('') is None
    assert jwt_mod.token_minutes_remaining('a.b') is None


def test_token_minutes_remaining_no_exp_claim():
    seg = base64.urlsafe_b64encode(json.dumps({'foo': 'bar'}).encode()).rstrip(b'=').decode()
    tok = f'header.{seg}.sig'
    assert jwt_mod.token_minutes_remaining(tok) is None
