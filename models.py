from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from database import Base

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    section_name = Column(String)  # e.g., "Polo Wall"
    tasks_completed = Column(JSON) # List of strings
    notes = Column(String, nullable=True)
    sales_amount = Column(Float)
    photo_path = Column(String)    # Path to the image file
    timestamp = Column(DateTime, default=datetime.utcnow)