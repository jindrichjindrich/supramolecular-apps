# Supramolecular.org apps API

Developer documentation coming soon.

## Installation

* `git clone <repository-url>` this repository
* change into the new directory
* `pip install -r requirements.txt`

###
echo disabled all haystack occurrences - bindift.views, supramolecular.settings, search_indexes
echo add to supramolecular.settings SITE_ID = 1
echo change supramolecular.settings DATABASES settings:
psql -U postgres -c "CREATE USER supra PASSWORD 'supra'"
psql -U postgres -c "CREATE DATABASE supra OWNER supra"

echo create django apps tables:
python manage.py migrate

echo create superuser (all 'supra'):
python manage.py createsuperuser 
###


## Running development server

* `python manage.py runserver`
* This will serve the app at [http://localhost:8000](http://localhost:8000)
  by default.

## Help:
## http://supramolecular.org/help-and-guides/app-guides/