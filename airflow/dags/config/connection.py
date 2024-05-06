from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import psycopg2

class Enginecreater():
    def __init__(self):
        db_user = 'postgres'
        db_password = 'abc123'
        db_host = 'localhost'
        db_port = 5432
        db_name = 'profiler'
        self.engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
        self.session = Session(self.engine)