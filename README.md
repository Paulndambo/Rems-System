# REMS System

REMS System is a Django-based real estate management application for managing rental properties, tenants, unit bills, rent payments, water bills, garbage bills, security deposits, expenses, reports, and notifications.

## Features

- User and role management for landlords, tenants, caretakers, listers, and house managers
- Property and unit management
- Tenant onboarding and next-of-kin records
- Rent, water, garbage, and security deposit billing
- Unit monthly bill generation and payment collection
- Expense tracking
- Maintenance request tracking
- Monthly rent and water payment reports
- WhatsApp notification support
- CSV report generation
- Django admin interface

## Tech Stack

- Python
- Django
- Django REST Framework
- SQLite for local development
- WhiteNoise for static files
- Cloudinary and Firebase integration helpers
- Coverage.py for test coverage reporting

## Project Structure

```text
RemsSystem/
|-- Rems/                  # Django project settings and root URLs
|-- apps/
|   |-- core/              # Shared models, dashboard views, constants, utilities
|   |-- users/             # Custom user model, auth, user management
|   |-- tenants/           # Tenant records and onboarding logic
|   |-- properties/        # Properties, units, water bills, maintenance requests
|   |-- payments/          # Rent, water, garbage, deposits, unit bill payments
|   |-- reports/           # Reports and CSV helpers
|   `-- notifications/     # Message templates and WhatsApp notification logic
|-- templates/             # Django templates
|-- static/                # Source static assets
|-- staticfiles/           # Collected static assets
|-- manage.py
|-- requirements.txt
`-- Dockerfile
```

## Getting Started

### Prerequisites

- Python 3.11 or newer is recommended
- `pip`
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd RemsSystem
```

### 2. Create and Activate a Virtual Environment

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations

```bash
python manage.py migrate
```

### 5. Create an Admin User

```bash
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

Open the app at:

```text
http://127.0.0.1:8000/
```

The admin site is available at:

```text
http://127.0.0.1:8000/admin/
```

## Running Tests

Run the full Django test suite:

```bash
python manage.py test
```

Run tests with coverage:

```bash
python -m coverage run --source=apps manage.py test
python -m coverage report --omit="*/migrations/*","*/tests.py"
```

Generate an HTML coverage report:

```bash
python -m coverage html
```

Then open:

```text
htmlcov/index.html
```

## Static Files

For production-style static file collection:

```bash
python manage.py collectstatic
```

The project uses WhiteNoise with compressed manifest static file storage.

## Docker

Build the image:

```bash
docker build -t rems-system .
```

Run the container:

```bash
docker run -p 8000:8000 rems-system
```

The container starts Gunicorn on port `8000`.

## Environment and Configuration Notes

Current settings are defined in `Rems/settings.py`. The project currently uses SQLite by default:

```text
db.sqlite3
```

Before deploying, move sensitive values out of source code and into environment variables or a secret manager. This includes:

- `SECRET_KEY`
- Cloudinary credentials
- SMS API keys
- WhatsApp API keys
- Firebase credentials

Also ensure production deployments use:

- `DEBUG = False`
- A restricted `ALLOWED_HOSTS` list
- A production database
- Secure static and media file handling
- HTTPS

## Important URLs

- `/` - Landing page
- `/dashboard/` - Main dashboard
- `/users/login/` - Login
- `/properties/` - Properties
- `/properties/units/` - Units
- `/tenants/` - Tenants
- `/payments/monthly-unit-bills/` - Monthly unit bills
- `/payments/pending-bills/` - Pending bills
- `/reports/monthly-rent-report/` - Monthly rent report
- `/reports/water-bills-report/` - Water bills report
- `/admin/` - Django admin

## Development Notes

- The custom user model is `users.User`.
- Most business entities inherit from `apps.core.models.AbstractBaseModel`.
- Phone numbers are normalized through `apps.core.clean_phone_number.clean_phone_number`.
- Unit monthly bill payment allocation is handled by `apps.payments.unit_bills.payment_processor.ProcessTenantPayment`.
- Water bill calculations live in `apps.properties.models.WaterBill`.
- CSV report writing lives in `apps.reports.utils.generate_csv`.

## Quality Checks

Before opening a pull request or deploying changes, run:

```bash
python manage.py test
python -m coverage run --source=apps manage.py test
python -m coverage report --omit="*/migrations/*","*/tests.py"
```

## License

No license file is currently included. Add one before distributing or open-sourcing the project.
