from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask import jsonify, make_response


def roleCheck(role):
    def innerRole(function):
        @wraps(function)
        def decorator(*arguments, **keywordArguments):
            try:
                verify_jwt_in_request()
            except NoAuthorizationError:
                return make_response(jsonify(msg="Missing Authorization Header"), 401)

            claims = get_jwt()
            if (("roles" in claims) and (role in claims["roles"])):
                return function(*arguments, **keywordArguments)
            else:
                return make_response(jsonify(msg="Missing Authorization Header"), 401)

        return decorator

    return innerRole
