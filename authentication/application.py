from flask import Flask, request, jsonify, make_response, Response
from configuration import Configuration
from models import database, User, UserRole
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from adminDecorator import roleCheck
import re

application = Flask(__name__)
application.config.from_object(Configuration)


def invalidJMBG(jmbg):
    if (len(jmbg) != 13):
        return True

    try:
        day = int(jmbg[0:2])
        if (day < 1 or day > 31):
            return True

        month = int(jmbg[2:4])
        if (month < 1 or month > 12):
            return True

        year = int(jmbg[4:7])
        if (year < 0 or year > 999):
            return True

        rr = int(jmbg[7:9])
        if (rr < 70 or rr > 99):
            return True

        bbb = int(jmbg[9:12])
        if (bbb < 0 or bbb > 999):
            return True
        # DDMMYYYRRBBBK
        # abcdefghijklm
        # m = 11 − (( 7×(a + g) + 6×(b + h) + 5×(c + i) + 4×(d + j) + 3×(e + k) + 2×(f + l) ) mod 11)

        a = int(jmbg[0])
        b = int(jmbg[1])
        c = int(jmbg[2])
        d = int(jmbg[3])
        e = int(jmbg[4])
        f = int(jmbg[5])
        g = int(jmbg[6])
        h = int(jmbg[7])
        i = int(jmbg[8])
        j = int(jmbg[9])
        k = int(jmbg[10])
        l = int(jmbg[11])

        calculated_k = 11 - ((7*(a + g) + 6*(b + h) + 5*(c + i) + 4*(d + j) + 3*(e + k) + 2*(f + l)) % 11)
        calculated_k = calculated_k if calculated_k != 10 else 0
        k = int(jmbg[12:13])
        if (k != calculated_k):
            return True
    except ValueError:
        return True

    return False


def invalidPassword(password):
    if len(password) < 8:
        return True

    regexNum = re.compile('[0-9]')
    regexUpper = re.compile('[A-Z]')
    regexLower = re.compile('[a-z]')

    if  regexNum.search(password) == None or regexUpper.search(password) == None or \
            regexLower.search(password) == None:
        return True

    return False


@application.route("/register", methods=["POST"])
def register():
    jmbg = request.json.get("jmbg", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    jmbgEmpty = len(jmbg) == 0
    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    msg = "Field {} is missing."

    if jmbgEmpty:
        return make_response(jsonify(message=msg.format("jmbg")), 400)
    elif forenameEmpty:
        return make_response(jsonify(message=msg.format("forename")), 400)
    elif surnameEmpty:
        return make_response(jsonify(message=msg.format("surname")), 400)
    elif emailEmpty:
        return make_response(jsonify(message=msg.format("email")), 400)
    elif passwordEmpty:
        return make_response(jsonify(message=msg.format("password")), 400)



    # validate jmbg
    if invalidJMBG(jmbg):
       return make_response(jsonify(message="Invalid jmbg."), 400)


    if not re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email):
        return make_response(jsonify(message="Invalid email."), 400)

    if invalidPassword(password):
        return make_response(jsonify(message="Invalid password."), 400)

    user = User(jmbg=jmbg, email=email, password=password, forename=forename, surname=surname)
    try:
        database.session.add(user)
        database.session.commit()
    except IntegrityError:
        return make_response(jsonify(message="Email already exists."), 400)

    userRole = UserRole(userId=user.id, roleId=2)
    database.session.add(userRole)
    database.session.commit()

    return Response(status=200)


jwt = JWTManager(application)


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    msg = "Field {} is missing."

    if emailEmpty:
        return make_response(jsonify(message=msg.format("email")), 400)
    elif passwordEmpty:
        return make_response(jsonify(message=msg.format("password")), 400)

    if not re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email):
        return make_response(jsonify(message="Invalid email."), 400)

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        return make_response(jsonify(message="Invalid credentials."), 400)

    additionalClaims = {
        "jmbg": user.jmbg,
        "forename": user.forename,
        "surname": user.surname,
        "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    # return make_response(accessToken, 200)
    # jsonify sama pravi access token
    return make_response(jsonify(accessToken=accessToken, refreshToken=refreshToken), 200)


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "surname": refreshClaims["surname"],
        "forename": refreshClaims["forename"],
        "roles": refreshClaims["roles"]
    }

    return make_response(
        jsonify(accessToken=create_access_token(identity=identity, additional_claims=additionalClaims)),
        200)


@application.route("/delete", methods=["POST"])
@roleCheck(role="admin")
def delete():
    identity = get_jwt_identity()
    email = request.json.get("email", "")

    if len(email) == 0:
        return make_response(jsonify(message="Field email is missing."), 400)

    if not re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email):
        return make_response(jsonify(message="Invalid email."), 400)

    user = User.query.filter(and_(User.email == email)).first()

    if not user:
        return make_response(jsonify(message="Unknown user."), 400)

    database.session.delete(user)
    database.session.commit()

    return Response(status=200)


if (__name__ == "__main__"):
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)
