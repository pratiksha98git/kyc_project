import pymongo

def get_db():
    # Connect to MongoDB running locally on default port
    client = pymongo.MongoClient("mongodb://localhost:27017/")

    # Create or connect to database
    db = client['kyc_db']

    
    db['users'].create_index('username', unique=True)
    db['kyc_data'].create_index('username')

    return db
