
# This file contains helper functions for MongoDB models
from flask import current_app
from bson import ObjectId

class User:
    """Helper class for user operations with MongoDB"""
    @staticmethod
    def get_by_id(user_id):
        """Get a user by ID"""
        from app import mongo
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                return None
        return mongo.db.users.find_one({"_id": user_id})
    
    @staticmethod
    def get_by_email(email):
        """Get a user by email"""
        from app import mongo
        return mongo.db.users.find_one({"email": email})
    
    @staticmethod
    def is_authenticated(user):
        """Check if user is authenticated"""
        return user is not None
