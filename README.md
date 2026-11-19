# Job Application Tracker

A full-stack web app for tracking job applications. It stores companies, job postings, applications, and contacts in MySQL, with a Flask backend and HTML/CSS frontend. A Job Match page ranks jobs by how many of their required skills you have.

Built for COP4751 (Course Project).

## Features

- **Dashboard**: totals for applications, interviews, offers, jobs, companies, and contacts; an applications-by-status breakdown; and the five most recent applications. All numbers come from live queries.
- **Companies, Jobs, Applications, Contacts**: list, add, edit, and delete for all four tables. Deleting asks for confirmation first.
- **Job Match**: enter your skills and see jobs ranked by match percentage, with the skills you are missing.
- **Validation**: required fields, minimum salary not above maximum salary, valid JSON for interview data, a valid email format, LinkedIn URLs that start with `http(s)://`, and statuses restricted to the allowed values.

## Tech stack

- Python 3 and Flask
- MySQL 8 (`mysql-connector-python`)
- HTML and CSS (no frameworks)

## Setup

1. **Clone the repository**
   ```
   git clone <YOUR-REPO-URL>
   cd job_tracker
   ```
2. **Create the database.** `schema.sql` creates the `job_tracker` database and all tables.
   ```
   mysql -u root -p < schema.sql
   ```
3. **Install the dependencies** (a virtual environment is recommended)
   ```
   pip install -r requirements.txt
   ```
4. **Set the environment variables.** The app reads the database password and Flask secret key from the environment, so no secrets are stored in the code.

   Windows PowerShell:
   ```
   $env:DB_PASSWORD = "your-mysql-password"
   $env:FLASK_SECRET_KEY = "any-long-random-string"
   ```
   macOS / Linux:
   ```
   export DB_PASSWORD="your-mysql-password"
   export FLASK_SECRET_KEY="any-long-random-string"
   ```
   The app connects to MySQL on `localhost` as `root`. If your setup differs, edit `database.py`.
5. **Run the app**
   ```
   python app.py
   ```
   Open http://127.0.0.1:5000 in your browser.

`schema.sql` contains the table structure only. Add a few companies and jobs through the app first (enter a job's required skills as a comma-separated list, such as `Python, SQL, Flask`), then try the Dashboard and Job Match.

## Project structure

```
job_tracker/
├── app.py            # Flask routes and validation
├── database.py       # MySQL connection
├── schema.sql        # Recreates the database
├── requirements.txt  # Python dependencies
├── AI_USAGE.md       # GenAI documentation
├── README.md
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── companies.html, company_form.html
    ├── jobs.html, job_form.html
    ├── applications.html, application_form.html
    ├── contacts.html, contact_form.html
    └── job_match.html
```

## Database design

| Table | Purpose | Key columns |
|---|---|---|
| `companies` | Employers | `company_id` (PK), `company_name`, `industry`, `website`, `city`, `state`, `notes` |
| `jobs` | Job postings | `job_id` (PK), `company_id` (FK), `job_title`, `job_type` (ENUM), `salary_min`, `salary_max`, `requirements` (JSON) |
| `applications` | Your applications | `application_id` (PK), `job_id` (FK), `application_date`, `status` (ENUM), `interview_data` (JSON) |
| `contacts` | People at companies | `contact_id` (PK), `company_id` (FK), `first_name`, `last_name`, `email`, `phone`, `linkedin_url` |

**Relationships:** one company has many jobs and many contacts, and one job has many applications.

**Delete behavior:** every foreign key uses `ON DELETE CASCADE`. Deleting a company also deletes its jobs, contacts, and (through the jobs) their applications. Deleting a job deletes its applications. The app tells the user when a delete cascades.

**Other design choices:**
- `jobs` has a unique key on `(company_id, job_title)` so the same posting can't be entered twice for one company.
- `jobs.requirements` stores the required skills as a JSON list, for example `["Python", "SQL", "Flask"]`. The Jobs form accepts a comma-separated string and converts it.
- `applications.interview_data` stores free-form interview details as JSON.

### Differences from the project spec

| Spec | This project | Why |
|---|---|---|
| `contacts.contact_name` | `first_name` and `last_name` | Needed for sorting and display |
| `contacts.title` | `contacts.job_title` | Consistency with the jobs table |
| `jobs.job_url` | `jobs.posting_url` | Longer length (500 characters) |
| Status: Applied, Screening, Interview, Offer, Rejected, Withdrawn | Applied, Phone screen, Interview completed, Offer accepted, Rejected, Withdrawn | More specific stages |
| - | Extra columns such as `created_at`, `is_active`, `job_description`, `response_date`, `interview_date`, `notes` | Useful tracking fields |

On the Dashboard, "interviews" counts the `Interview completed` status and "offers" counts `Offer accepted`.

## How Job Match works

For each job with listed requirements:

1. Skills are compared case-insensitively and ignoring extra spaces, so `python` and `Python ` match.
2. **Match percentage = matched skills / required skills × 100**, rounded to a whole number.
3. Missing skills are listed under each job.
4. Jobs are sorted from the highest match to the lowest, and jobs that share no skills with you are left out.

Example: with the skills `Python, SQL, Flask`, a job requiring Python, SQL, and Flask scores 100% (3/3). A job requiring Python, SQL, and Tableau scores 67% (2/3), with Tableau missing.

## Security notes

- All SQL uses parameterized queries (`%s` placeholders) to prevent SQL injection.
- The database password and Flask secret key come from environment variables, not the source code.

## GenAI usage

See [AI_USAGE.md](AI_USAGE.md) for the tools, prompts, and changes made to AI-generated code.
