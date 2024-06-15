import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

firebase_admin.initialize_app(credentials.Certificate('firebase_auth.json')) # Initialize Firebase Admin SDK
db = firestore.client()  # Access Firestore database

def get_or_create_user(username):
    users_ref = db.collection('users')     # Reference to the 'users' collection
    query = users_ref.where('username', '==', username)      # Query the collection to check if the username exist
    results = query.get()

    if results: # Username exists, retrieve the first document
        for doc in results:
            print(f'Found existing user with username {username}.')
            return doc._data

    else: # Username does not exist, create a new document
        new_doc_ref = users_ref.document()
        new_doc_ref.set({
            'username': username,
            'created_at': firestore.SERVER_TIMESTAMP,
            'last modified_at': firestore.SERVER_TIMESTAMP,
            'Paths': []
        })
        print(f'Created new user with username {username}.')
        return new_doc_ref.id, {'username': username}  # Return document ID and data