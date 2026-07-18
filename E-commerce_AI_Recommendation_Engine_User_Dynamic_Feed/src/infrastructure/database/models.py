from sqlalchemy import Column, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # Storing category weights for the dot-product calculation
    weight_running = Column(Float, default=0.0)
    weight_weightlifting = Column(Float, default=0.0)
    weight_outdoor = Column(Float, default=0.0)

class UserAffinity(Base):
    __tablename__ = "user_affinities"
    
    user_id = Column(String, primary_key=True, index=True)
    # Storing the AI's calculated scores
    score_running = Column(Float, default=0.33)
    score_weightlifting = Column(Float, default=0.33)
    score_outdoor = Column(Float, default=0.33)