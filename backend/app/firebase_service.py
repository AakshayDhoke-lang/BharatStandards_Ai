from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any


def _clean_private_key(value: str) -> str:
    return value.replace('\\n', '\n').strip()


def _service_account_from_env() -> dict[str, Any] | None:
    raw = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip()
    if raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f'FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON: {exc}') from exc
        if not isinstance(data, dict):
            raise RuntimeError('FIREBASE_SERVICE_ACCOUNT_JSON must contain one JSON object.')
        if data.get('private_key'):
            data['private_key'] = _clean_private_key(str(data['private_key']))
        return data

    project_id = os.getenv('FIREBASE_PROJECT_ID', '').strip()
    client_email = os.getenv('FIREBASE_CLIENT_EMAIL', '').strip()
    private_key = os.getenv('FIREBASE_PRIVATE_KEY', '').strip()
    if project_id and client_email and private_key:
        return {
            'type': 'service_account',
            'project_id': project_id,
            'private_key_id': os.getenv('FIREBASE_PRIVATE_KEY_ID', '').strip(),
            'private_key': _clean_private_key(private_key),
            'client_email': client_email,
            'client_id': os.getenv('FIREBASE_CLIENT_ID', '').strip(),
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            'client_x509_cert_url': os.getenv('FIREBASE_CLIENT_CERT_URL', '').strip(),
            'universe_domain': 'googleapis.com',
        }
    return None


def firebase_admin_configured() -> bool:
    if os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip():
        return True
    if all(os.getenv(k, '').strip() for k in ('FIREBASE_PROJECT_ID', 'FIREBASE_CLIENT_EMAIL', 'FIREBASE_PRIVATE_KEY')):
        return True
    path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', '').strip()
    return bool(path and os.path.exists(path))


@lru_cache(maxsize=1)
def get_firebase_app():
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError as exc:
        raise RuntimeError('firebase-admin is not installed in the backend environment.') from exc

    if firebase_admin._apps:
        return firebase_admin.get_app()

    env_credential = _service_account_from_env()
    if env_credential:
        return firebase_admin.initialize_app(credentials.Certificate(env_credential))

    path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', '').strip()
    if path:
        if not os.path.exists(path):
            raise RuntimeError(f'FIREBASE_SERVICE_ACCOUNT_PATH does not exist: {path}')
        return firebase_admin.initialize_app(credentials.Certificate(path))

    # This also supports Google Application Default Credentials when available.
    try:
        return firebase_admin.initialize_app()
    except Exception as exc:
        raise RuntimeError(
            'Firebase Admin is not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON on Vercel '
            'or FIREBASE_PROJECT_ID + FIREBASE_CLIENT_EMAIL + FIREBASE_PRIVATE_KEY.'
        ) from exc


@lru_cache(maxsize=1)
def get_firestore_client():
    try:
        from firebase_admin import firestore
    except ImportError as exc:
        raise RuntimeError('firebase-admin is not installed in the backend environment.') from exc
    get_firebase_app()
    return firestore.client()


def verify_firebase_id_token(id_token: str) -> dict[str, Any]:
    if not id_token.strip():
        raise RuntimeError('Firebase ID token is empty.')
    try:
        from firebase_admin import auth
    except ImportError as exc:
        raise RuntimeError('firebase-admin is not installed in the backend environment.') from exc
    get_firebase_app()
    try:
        return auth.verify_id_token(id_token)
    except Exception as exc:
        raise RuntimeError('Invalid or expired Firebase ID token.') from exc


def firestore_health() -> dict[str, Any]:
    configured = firebase_admin_configured()
    if not configured:
        return {
            'ok': False,
            'configured': False,
            'projectId': os.getenv('FIREBASE_PROJECT_ID') or None,
            'message': 'Firebase Admin credentials are not configured for this backend runtime.',
        }
    try:
        client = get_firestore_client()
        # A single lightweight read proves that credentials can reach Firestore without mutating data.
        list(client.collection('_system_health').limit(1).stream())
        return {
            'ok': True,
            'configured': True,
            'projectId': getattr(client, 'project', None) or os.getenv('FIREBASE_PROJECT_ID') or None,
            'message': 'Firestore connection is available.',
        }
    except Exception as exc:
        return {
            'ok': False,
            'configured': True,
            'projectId': os.getenv('FIREBASE_PROJECT_ID') or None,
            'message': f'Firestore connection failed: {type(exc).__name__}: {exc}',
        }
