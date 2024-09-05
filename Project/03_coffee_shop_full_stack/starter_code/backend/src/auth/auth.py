import json
from flask import request, _request_ctx_stack, jsonify
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'mikilade.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'https://csfsauth'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

def get_token_auth_header():
    """Parse the access token from the auth header."""

    # GET auth header from incoming request
    auth_header = request.headers.get('Authorization', None)

    # Raise error if auth header is missing.
    if not auth_header :
        raise AuthError(
            {
                'code': 'missing_auth_header',
                'description': 'An authorization header was expected but is missing.'
            }, 401
        )
    
    # We expect the auth header to be in format "Bearer <token>"
    header_parts = auth_header.split()

    # Throw a 401 if bearer is not in the header
    if header_parts[0].lower() != 'bearer':
        raise AuthError(
            {
                'code': 'invalid_header',
                'description': 'The authorization header must be prefaced with Bearer.'
            }, 401
        )
    # Throw a 401 if there is no bearer string in token
    elif len(header_parts) == 1:
        raise AuthError(
            {
                'code': 'invalid_header',
                'description': 'The token was not found.'
            }
        )
    elif len(header_parts) > 2:
        raise AuthError(
            {
                'code': 'invalid_header',
                'description': 'The authorization header must be the bearer token specifically.'
            }
        )
    
    # Return the token as it is valid
    jwt_token = header_parts[1]
    return jwt_token


def check_permissions(permission, payload):
    """Verify the proper permissions are in the JWT payload."""
    # Check that the 'permissions' key is in payload, raise 403 if so
    if 'permissions' not in payload:
        raise AuthError(
            {
                'code': 'invalid_claims',
                'description': 'Permissions were not found within the JWT.'
            }, 403
        )

    # Check the required permission within the permissions list, raise 403 if unauthorized
    if permission not in payload['permissions']:
        raise AuthError(
            {
                'code': 'unauthorized',
                'description': 'Permission was not found.'
            }, 403
        )
    
    # Permissions exist both in the payload and in the permissions list
    return True

def verify_decode_jwt(token):
    """Verify and decode the JWT token from Auth0"""

    # Get the public key from the JWKS endpoint in Auth0
    rawurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(rawurl.read())

    # Get header from token
    raw_header = jwt.get_unverified_header(token)

    # Verify Key ID in token
    if 'kid' not in raw_header:
        # raise an auth error for malformation
        raise AuthError(
            {
                'code': 'invalid_header',
                'description': 'Authorization was malformed, no Key ID found.'
            }, 401
        )
    
    # Find the public key matching the token Key ID
    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == raw_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    
    if rsa_key:
        try:
            # Verify JWT with public key
            payload = jwt.decode(token, rsa_key, algorithms=ALGORITHMS, audience=API_AUDIENCE, issuer=f'https://{AUTH0_DOMAIN}/')
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'The provided token is expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'The provided claims were incorrect. Verify audience and issuer.'
            }, 401)

        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'The authentication token was unable to be parsed.'
            }, 400)
    
    else:
        # Raise an AuthError for miscellaneous error
        raise AuthError({
            'code': 'invalid_header',
            'description': 'An appropriate key was unable to be found.'
        }, 400)
            

def requires_auth(permission=''):
    """Wrapper to a function that checks if the user is authorized to run it, and throws an AuthError exception if not."""
    def requires_auth_decorator(f):
        """Helper function of the above that actually wraps the function."""
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                token = get_token_auth_header()
                payload = verify_decode_jwt(token)
                check_permissions(permission, payload)
            except AuthError as e:
                # Handle auth errors and return response code
                return jsonify(
                    {
                        'success': False,
                        'error': e.status_code,
                        'message': e.error['description']
                    }
                ), e.status_code
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator