import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# initialize DB
db_drop_and_create_all()

# ROUTES

@app.route('/drinks', methods=['GET'])
def get_drinks():
    """Query all drinks from db. Public endpoint."""
    try:
        # Query all drinks from db
        drinks = Drink.query.all()

        # Cast the drink into the short representation w/ list comprehension
        drinks_short = [drink.short() for drink in drinks]

        # Return success w/ drink list
        return jsonify(
            {
                'success': True,
                'drinks': drinks_short
            }
        ), 200
    
    except Exception as e:
        # Log unexpected error. Return a 500 status code.
        print(f'Error occurred: {e}')

        return jsonify(
            {
                'success': False,
                'message': 'An error occurred while querying drinks.'
            }
        ), 500


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    """Query all drink details. Requires get:drinks-detail permission."""
    try:
        # Query all drinks from db
        drinks = Drink.query.all()

        # Cast the drink into the long representation w/ list comprehension
        drinks_long = [drink.long() for drink in drinks]

        # Return success w/ drink list
        return jsonify(
            {
                'success': True,
                'drinks': drinks_long
            }
        ), 200
    
    except Exception as e:
        # Log unexpected error. Return a 500 status code.
        print(f'Error occurred: {e}')

        return jsonify(
            {
                'success': False,
                'message': 'An error occurred while querying drinks.'
            }
        ), 500


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    """Create a new drink. Requires a post:drinks permission."""
    try:
        # Parse request data, should have title and recipe
        raw_data = request.get_json()

        drink_title = raw_data.get('title', None)
        drink_recipe = raw_data.get('recipe', None)

        # Throw a 400 if no title or recipe
        if not drink_title or not drink_recipe:
            abort(400, description='Drink title and recipe are required!')

        # Cast recipe to JSON
        drink_recipe_json = json.dumps(drink_recipe)

        # Create Drink object
        new_drink = Drink(title=drink_title, recipe = drink_recipe_json)

        # Insert drink into db
        new_drink.insert()

        # Return new drink details in long format
        return jsonify(
            {
                'success': True,
                'drinks': [new_drink.long()]
            }
        ), 200
    except Exception as e:
        print(f'Error occurred: {e}')

        return jsonify(
            {
                'success': False,
                'message': 'An error occurred while creating drink.'
            }
        ), 500

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    """Update an existing drink. Requires a patch:drinks permission."""
    try:
        # Query drink by ID
        drink = Drink.query.filter_by(id=id).one_or_none()

        # if drink DNE, return 404
        if drink is None:
            abort(404, description=f'Drink with id {id} was not found.')
        
        # Parse request data, should have title and recipe
        raw_data = request.get_json()

        drink_title = raw_data.get('title', None)
        drink_recipe = raw_data.get('recipe', None)

        # Update title and/or recipe if provided
        if drink_title:
            drink.title = drink_title

        if drink_recipe:
            drink.recipe = json.dumps(drink_recipe) # Recipe casted to JSON

        # Save to DB
        drink.update()

        # Return updated drink details in long format
        return jsonify(
            {
                'success': True,
                'drinks': [drink.long()]
            }
        ), 200
    except Exception as e:
        print(f'Error occurred: {e}')

        return jsonify(
            {
                'success': False,
                'message': 'An error occurred while updating drink.'
            }
        ), 500


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    """Delete an existing drink. Requires a delete:drinks permission."""
    try:
        # Query drink by ID
        drink = Drink.query.filter_by(id=id).one_or_none()

        # if drink DNE, return 404
        if drink is None:
            abort(404, description=f'Drink with id {id} was not found.')

        # Delete from DB
        drink.delete()

        # Return updated drink details in long format
        return jsonify(
            {
                'success': True,
                'delete': id
            }
        ), 200
    except Exception as e:
        print(f'Error occurred: {e}')

        return jsonify(
            {
                'success': False,
                'message': 'An error occurred while deleting drink.'
            }
        ), 500
# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable!"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found!"
    }), 404


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized!"
    }), 401

@app.errorhandler(403)
def permission_not_found(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "permission not found!"
    }), 403