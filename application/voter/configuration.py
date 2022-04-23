import os

databaseURL = os.environ["DATABASE_URL"]
class Configuration():
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseURL}/electionsdatabase"
    REDIS_HOST = "redis"
    REDIS_VOTES_LIST = "votes"
    JWT_SECRET_KEY = "dfjnewpcirmvrnefsifmt"