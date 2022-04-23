from flask import Flask, request, make_response, jsonify, Response
from configuration import Configuration
from models import database, Election, Vote
from redis import Redis
from datetime import datetime, timedelta
from dateutil import parser
import pytz
application = Flask(__name__)
application.config.from_object(Configuration)


def createInvalid(guid, electionOfficialJmbg, pollNumber, election, reason):
    vote = Vote(guid=guid, electionOfficialJmbg=electionOfficialJmbg, pollNumber=pollNumber, electionId=election,
                reason=reason, valid=False)
    database.session.add(vote)
    database.session.commit()

if __name__=="__main__":
    database.init_app(application)
    with application.app_context():
        while True:
            with Redis(host=Configuration.REDIS_HOST) as redis:
                _, vote = redis.blpop(Configuration.REDIS_VOTES_LIST)
                message = vote.decode("utf-8")
                elements = message.split(';')
                electionOfficialJmbg = elements[0]
                guid = elements[1]
                pollNumber = int(elements[2])
                currentTime = parser.isoparse(elements[3])
                elections = Election.query.all()

                currentTime = currentTime.replace(tzinfo=None)

                election = None
                for e in elections:
                    print(currentTime)
                    # print("Start: {}".format(e.start), "Kraj: {}".format(e.end))
                    if (e.start < currentTime and e.end > currentTime ):
                        election = e

                if not election:
                    print("Preskoceno")
                    continue

                # print("Proslo")

                sameGuid = Vote.query.filter(Vote.guid == guid).first()

                if not sameGuid and not (len(election.participants) < pollNumber):
                    voteO = Vote(guid=guid, electionOfficialJmbg=electionOfficialJmbg, pollNumber=pollNumber, electionId=election.id, valid=True)
                    database.session.add(voteO)
                    database.session.commit()
                elif sameGuid:
                    createInvalid(guid, electionOfficialJmbg, pollNumber, election.id, "Duplicate ballot.")
                elif len(election.participants) < pollNumber:
                    createInvalid(guid, electionOfficialJmbg, pollNumber, election.id, "Invalid poll number.")
