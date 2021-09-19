import os
from app import db
from app.models.dummy_data import main


def delete_and_create_db():
	os.system('rm -rf migrations; rm app/models/database.db; flask db init; flask db migrate -m "First migration"; flask db upgrade')
        
        
def reset(development=True):
    delete_and_create_db()
    main(development)


