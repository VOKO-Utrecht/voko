# VOKO
Django based custom web application for food collective www.vokoutrecht.nl.

![example workflow](https://github.com/VOKO-Utrecht/voko/actions/workflows/ci.yml/badge.svg)

## Some notes
1. The code base needs cleaning up and adding of tests.
2. License: GNU GPLv3
3. Use at your own risk, no support.


# Development environment using Docker
### Quick Setup (Recommended)
**Option 1: Using make (if you have make installed)**
```bash
git clone https://github.com/VOKO-Utrecht/voko.git
cd voko
make setup
```

**Option 2: Using docker-compose directly**
```bash
git clone https://github.com/VOKO-Utrecht/voko.git
cd voko
docker-compose up
```

Then:
4. Wait for the setup to complete (you'll see "Starting development server...")
5. Go to: http://127.0.0.1:8000
6. Login with: `admin@voko.local` / `admin123`

That's it! The setup automatically:
- Creates and initializes the database
- Runs all migrations
- Creates a superuser account if it does not exist
- Starts the development server

You can also visit the main site at: http://127.0.0.1:8000/

### Common Commands
If you have make installed, you can use these convenient commands:
- `make setup` - Complete setup (build and start)
- `make up` - Start services
- `make down` - Stop services
- `make logs` - View logs
- `make shell` - Access Django shell
- `make test` - Run tests
- `make validate` - Check if setup is working
- `make reset` - Reset database (deletes all data)
- `make help` - Show all available commands

#### Customizing the auto-setup
You can customize the automatically created superuser by setting environment variables:
- `DJANGO_SUPERUSER_EMAIL` (default: admin@voko.local)
- `DJANGO_SUPERUSER_FIRST_NAME` (default: Admin)
- `DJANGO_SUPERUSER_LAST_NAME` (default: User)
- `DJANGO_SUPERUSER_PASSWORD` (default: admin123)

For convenience, you can copy `.env.example` to `.env` and modify the values there:
```bash
cp .env.example .env
# Edit .env file with your preferred values
```

Or set them directly when starting:
```bash
DJANGO_SUPERUSER_EMAIL=myemail@example.com DJANGO_SUPERUSER_PASSWORD=mypassword docker-compose up
```

### Troubleshooting
- If you get database connection errors, make sure the database is fully started by running `docker-compose up db` first, waiting for it to be ready, then stopping it and running `docker-compose up` again.
- If you need to reset the database, run: `docker-compose down -v` (this will delete all data)
- To access the Django shell: `docker exec -it voko_web bash` then `./manage.py shell --settings=vokou.settings.development`
- To view logs: `docker-compose logs web` or `docker-compose logs db`
- To validate your setup is working: `./validate_setup.sh`

## What's New in This Setup?
This improved Docker setup includes:
- **Automated superuser creation**: No need to manually create admin accounts
- **Automatic sample data creation**: Creates a sample supplier and order round
- **One-command setup**: Just run `docker-compose up` or `make setup`
- **Health checks**: Ensures database is ready before starting the web server
- **Validation script**: Check if everything is working correctly
- **Convenient Make commands**: Easy-to-use shortcuts for common tasks
- **Environment variable support**: Customize superuser credentials and other settings
- **Better error handling**: More robust startup process


# Development environment without Docker
1. Run: pip install --user uv
2. Run: `git clone https://github.com/VOKO-Utrecht/voko.git`
3. Run: `cd voko`
4. Sync environment: `uv sync --dev`
6. Active environment: `source .venv/bin/activate`


### Set up sqlite database, create superuser and automatically create first order round
    python manage.py makemigrations --settings=vokou.settings.development
    python manage.py migrate --settings=vokou.settings.development
    python manage.py createsuperuser --settings=vokou.settings.development
    python manage.py runcrons --force --settings=vokou.settings.development

### Run tests
    python manage.py test --settings=vokou.settings.testing

### Run development server
    python manage.py runserver --settings=vokou.settings.development

### Adding user
1. Register as new user at: http://localhost:8000/accounts/register/
2. Look up the confirmation token at: http://localhost:8000/admin/accounts/emailconfirmation/
3. Visit (replace TOKEN with copied token): http://localhost:8000/accounts/register/confirm/TOKEN
4. Log in as superuser and go to user admin: http://localhost:8000/admin/accounts/vokouser/
5. Select your user, choose in dropdown: "Gebruikersactivatie na bezoek info-avond", click "Uitvoeren" button
6. Log out as superuser, or visit the next link incognito (replace TOKEN with copied token): http://localhost:8000/accounts/register/finish/TOKEN
7. Fill in fields and submit

## Marking member as sleeping member
1. Go to http://localhost:8000/admin/accounts/vokouser/
2. Select user
3. Choose in dropdown: "Anonimiseer account"
4. Click "Uitvoeren" button

## Re-activating sleeping member
1. Go to http://localhost:8000/admin/accounts/sleepingvokouser/
2. Open user
3. De-tick "Sleeping (inactive) member"
4. click "OPSLAAN" button
