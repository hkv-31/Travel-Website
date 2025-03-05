from database import db

# Abstraction (Base class for TravelEntity)
class TravelEntity:
    def to_dict(self):
        raise NotImplementedError("Subclasses must implement this method")

# Destination Model (Single Inheritance)
class Destination(TravelEntity, db.Model):
    __tablename__ = 'destinations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)

    def __init__(self, name, description, location):
        self.name = name
        self.description = description
        self.location = location

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location
        }
