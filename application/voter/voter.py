from flask import Flask, request, make_response, jsonify, Response
from configuration import Configuration
from models import database
from redis import Redis
from roleDecorator import roleCheck
from flask_jwt_extended import JWTManager, get_jwt
import csv
import io
import pytz
from datetime import datetime, timezone

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

@application.route("/vote", methods=["POST"])
@roleCheck("voter")
def enterVote():
    file = request.files.get("file", "")

    if file == "":
        return make_response(jsonify(message="Field file is missing."), 400)

    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.reader(stream)

    claims = get_jwt()

    line = 0
    for row in reader:
        if len(row) != 2:
            return make_response(jsonify(message="Incorrect number of values on line {}.".format(line)),400)
        try:
            pollNumber = int(row[1])
        except: 
            return make_response(jsonify(message="Incorrect poll number on line {}.".format(line)), 400)

        if int(row[1]) < 1:
            return make_response(jsonify(message="Incorrect poll number on line {}.".format(line)), 400)

        with Redis(host=Configuration.REDIS_HOST) as redis:
            tz = pytz.timezone("Europe/Belgrade")
            dt_now = datetime.now(tz=tz)
            redis.rpush(Configuration.REDIS_VOTES_LIST, claims["jmbg"] + ';' + str(row[0]) + ';' + str(row[1]) + ';' + dt_now.isoformat())
            print(dt_now.isoformat())

        
    return Response(status = 200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host = "0.0.0.0", port=5000)
