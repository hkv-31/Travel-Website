from flask import Flask, jsonify, render_template
from database import db
from models import Destination
import logging

# Initialize Flask app
app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///travel.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with Flask app
db.init_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)


# **Home Page Route (Serves HTML)**
@app.route('/')
def home():
    return render_template('index.html')


# **API Route: Get All Destinations**
@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    try:
        destinations = Destination.query.all()
        return jsonify([dest.to_dict() for dest in destinations]), 200
    except Exception as e:
        logging.error(f"Error fetching destinations: {str(e)}")
        return jsonify({"error": "Failed to fetch destinations"}), 500


# **API Route: Get Destination by ID**
@app.route('/api/destination/<int:dest_id>', methods=['GET'])
def get_destination(dest_id):
    try:
        destination = Destination.query.get(dest_id)
        if destination:
            return jsonify(destination.to_dict()), 200
        else:
            return jsonify({"error": "Destination not found"}), 404
    except Exception as e:
        logging.error(f"Error fetching destination {dest_id}: {str(e)}")
        return jsonify({"error": "Failed to fetch destination"}), 500


# **API Route: Add a New Destination**
@app.route('/api/destination', methods=['POST'])
def add_destination():
    from flask import request

    try:
        data = request.json
        new_destination = Destination(
            name=data["name"],
            description=data["description"],
            location=data["location"]
        )

        db.session.add(new_destination)
        db.session.commit()
        return jsonify({"message": "Destination added successfully!"}), 201

    except Exception as e:
        logging.error(f"Error adding destination: {str(e)}")
        return jsonify({"error": "Failed to add destination"}), 500


# **API Route: Delete a Destination**
@app.route('/api/destination/<int:dest_id>', methods=['DELETE'])
def delete_destination(dest_id):
    try:
        destination = Destination.query.get(dest_id)
        if destination:
            db.session.delete(destination)
            db.session.commit()
            return jsonify({"message": "Destination deleted successfully!"}), 200
        else:
            return jsonify({"error": "Destination not found"}), 404

    except Exception as e:
        logging.error(f"Error deleting destination {dest_id}: {str(e)}")
        return jsonify({"error": "Failed to delete destination"}), 500


# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created before running
    app.run(debug=True)
