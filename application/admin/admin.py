from flask import Flask, request, Response, make_response, jsonify
from configuration import Configuration
from models import database, Participant, Election, ElectionParticipant, Vote
from adminDecorator import roleCheck
from flask_jwt_extended import JWTManager
from datetime import datetime
from dateutil import parser
from sqlalchemy import and_, or_, func
import pytz

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route("/createParticipant", methods=["POST"])
@roleCheck(role="admin")
def createParticipant():
    name = request.json.get("name", "")
    individual = request.json.get("individual", "")

    nameEmpty = len(name) == 0
    individualEmpty = type(individual) is str

    msg = "Field {} is missing."

    if nameEmpty:
        return make_response(jsonify(message=msg.format("name")), 400)
    elif individualEmpty:
        return make_response(jsonify(message=msg.format("individual")), 400)

    participant = Participant(name=name, individual=individual)

    database.session.add(participant)
    database.session.commit()

    return make_response(jsonify(id=participant.id), 200)


@application.route("/getParticipants", methods=["GET"])
@roleCheck(role="admin")
def getParticipants():
    participants = []
    for instance in Participant.query.all():
        participant = {"id": instance.id, "name": instance.name, "individual": instance.individual}
        participants.append(participant)

    return make_response(jsonify(participants = participants), 200)


@application.route("/createElection", methods=["POST"])
@roleCheck(role="admin")
def createElection():
    start = request.json.get("start", "")
    end = request.json.get("end", "")
    individual = request.json.get("individual", "")
    participants = request.json.get("participants", "")

    startEmpty = len(start) == 0
    endEmpty = len(end) == 0
    individualEmpty = type(individual) is str
    participantsEmpty = type(participants) is str

    msg = "Field {} is missing."

    if startEmpty:
        return make_response(jsonify(message=msg.format("start")), 400)
    elif endEmpty:
        return make_response(jsonify(message=msg.format("end")), 400)
    elif individualEmpty:
        return make_response(jsonify(message=msg.format("individual")), 400)
    elif participantsEmpty:
        return make_response(jsonify(message=msg.format("participants")), 400)

    try:
        startDate = parser.isoparse(start)
        endDate = parser.isoparse(end)
    except:
        return make_response(jsonify(message="Invalid date and time."), 400)

    if startDate >= endDate:
        return make_response(jsonify(message="Invalid date and time."), 400)

    elections = Election.query.all()

    noParticipants = len(participants) == 0

    for el in elections:
        if not (endDate < el.start or startDate > el.end):
            return make_response(jsonify(message="Invalid date and time."), 400)


    if len(participants) < 2:
        return make_response(jsonify(message="Invalid participants."), 400)

    numParticipants = 0
    for participant in Participant.query.filter(
            or_(
                *[Participant.id == par for par in participants]
            )
    ).all():
        numParticipants += 1
        if individual != participant.individual:
            return make_response(jsonify(message="Invalid participants."), 400)

    if numParticipants != len(participants):
        return make_response(jsonify(message="Invalid participants."), 400)

    allParticipants = Participant.query.all()

    # tz = pytz.timezone("Europe/Belgrade")
    # startDate = startDate.astimezone(tz=tz)
    # endDate = endDate.astimezone(tz=tz)
    election = Election(start=startDate, end=endDate, individual=individual)

    database.session.add(election)
    database.session.commit()

    pollNumbers = []
    for i in range(len(participants)):
        ep = ElectionParticipant(participantId=participants[i], electionId=election.id, pollNumber=i + 1)
        database.session.add(ep)
        database.session.commit()
        pollNumbers.append(i + 1)

    return make_response(jsonify(pollNumbers=pollNumbers), 200)


@application.route("/getElections", methods=["GET"])
@roleCheck(role="admin")
def getElections():
    elections = []
    for election in Election.query.all():
        electionDict = {"id": election.id, "start": election.start.isoformat(), "end": election.end.isoformat(),\
                        "individual": election.individual}

        participants = []
        for participant in election.participants:
            participants.append({"id": participant.id, "name": participant.name})

        electionDict["participants"] = participants

        elections.append(electionDict)

    return make_response(jsonify(elections=elections), 200)


@application.route("/getResults", methods=["GET"])
@roleCheck(role="admin")
def getResults():
    electionId = request.args.get("id", "")

    if len(str(electionId)) == 0:
        return make_response(jsonify(message="Field id is missing."), 400)

    election = Election.query.filter(Election.id == electionId).first()

    if not election:
        return make_response(jsonify(message="Election does not exist."), 400)

    tz = pytz.timezone("Europe/Belgrade")
    dt_now = datetime.now(tz=tz).replace(tzinfo=None)
    if election.end > dt_now:
        return make_response(jsonify(message="Election is ongoing."), 400)

    queryCountFunc = func.count(Vote.pollNumber)
    queryV = Vote.query.filter(and_(Vote.valid == True, Vote.electionId == electionId)).group_by(\
        Vote.pollNumber).with_entities(Vote.pollNumber, queryCountFunc)

    votes = queryV.all()

    totalVotes = 0
    for vote in votes:
        totalVotes += vote[1]

    electionParticipants = []
    if election.individual:
        for vote in votes:
            electionParticipant = {"pollNumber": vote[0], "name": election.participants[vote[0] - 1].name}
            result = round(float(vote[1]) / totalVotes, 2)
            electionParticipant["result"] = result
            electionParticipants.append(electionParticipant)
    else:
        votesAboveThreshold = []
        votesBelowThreshold = []
        assignedSeats = []
        for vote in votes:
            if (float(vote[1]) / totalVotes >= 0.05):
                votesAboveThreshold.append(vote)
                assignedSeats.append(0)
            else:
                votesBelowThreshold.append(vote)

        numSeats = 250
        for i in range(numSeats):
            maxQuot, maxQuotIndex = -1, 0
            for j in range(len(votesAboveThreshold)):
                quot = float(votesAboveThreshold[j][1]) / (assignedSeats[j] + 1)
                if quot > maxQuot:
                    maxQuot = quot
                    maxQuotIndex = j

            assignedSeats[maxQuotIndex] += 1

        electionParticipants = []
        for i in range(len(votesAboveThreshold)):
            electionParticipant = {"pollNumber": votesAboveThreshold[i][0],
                                   "name": election.participants[votesAboveThreshold[i][0] - 1].name,
                                   "result": assignedSeats[i]}
            electionParticipants.append(electionParticipant)

        for i in range(len(votesBelowThreshold)):
            electionParticipant = {"pollNumber": votesBelowThreshold[i][0],
                                   "name": election.participants[votesBelowThreshold[i][0] - 1].name, "result": 0}
            electionParticipants.append(electionParticipant)

    invalidVotes = []

    query = Vote.query.filter(
        and_(
            Vote.valid == False, Vote.electionId == electionId
        )
    )

    result = query.all()

    for vote in result:
        invalidVote = {"electionOfficialJmbg": vote.electionOfficialJmbg, "ballotGuid": vote.guid,
                        "pollNumber": vote.pollNumber, "reason": vote.reason}
        invalidVotes.append(invalidVote)

    return make_response(jsonify(participants=electionParticipants, invalidVotes=invalidVotes), 200)



if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5001)
