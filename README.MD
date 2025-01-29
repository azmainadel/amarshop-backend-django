# amarshop-backend

## Requirements

1. Make sure Docker and Docker Compose are installed

2. Make sure you have a virtual environment created and activated

## Running this project

### 1. Install the packages

`pip install -r requirements.txt`

### 2. Run the local database

Run this from the docker folder:

`docker-compose up -d`

### 3. Migrate the database

Run this from the root folder

`python manage.py migrate`

### 4. Run the Django project

Run this from the root folder

`python manage.py runserver`