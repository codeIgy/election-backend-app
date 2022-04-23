from datetime import timedelta
import os

databaseURL = os.environ["DATABASE_URL"]

class Configuration():
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseURL}/authenticationDB"
    JWT_SECRET_KEY = "dfjnewpcirmvrnefsifmt"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
