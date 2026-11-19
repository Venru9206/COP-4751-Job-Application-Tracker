# app.py
import json
import os
import re
import mysql.connector
from database import get_connection, calculate_match
from flask import Flask, abort, flash, redirect, render_template, request, url_for

from database import get_connection

app = Flask(__name__)

# Load the secret key from the environment instead of hardcoding it.
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Set the FLASK_SECRET_KEY environment variable before starting the app.")


def clean(value):
    """Turn blank form fields into None so they store as NULL."""
    value = (value or "").strip()
    return value or None


@app.route("/")
def index():
    return redirect(url_for("companies_list"))


# ---------- COMPANIES ----------

@app.route("/companies")
def companies_list():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM companies ORDER BY company_name")
    companies = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("companies.html", companies=companies)


@app.route("/companies/add", methods=["GET", "POST"])
def company_add():
    if request.method == "POST":
        form = request.form.to_dict()
        if not clean(form.get("company_name")):
            flash("Company name is required.", "error")
            return render_template("company_form.html", company=form, action="Add")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO companies (company_name, industry, website, city, state, notes)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (clean(form["company_name"]), clean(form.get("industry")),
             clean(form.get("website")), clean(form.get("city")),
             clean(form.get("state")), clean(form.get("notes"))),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Company added.", "success")
        return redirect(url_for("companies_list"))

    return render_template("company_form.html", company={}, action="Add")


@app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
def company_edit(company_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM companies WHERE company_id = %s", (company_id,))
    company = cur.fetchone()
    if company is None:
        cur.close()
        conn.close()
        abort(404)

    if request.method == "POST":
        form = request.form.to_dict()
        if not clean(form.get("company_name")):
            flash("Company name is required.", "error")
            cur.close()
            conn.close()
            return render_template("company_form.html", company=form, action="Edit")

        cur.execute(
            """UPDATE companies
               SET company_name=%s, industry=%s, website=%s, city=%s, state=%s, notes=%s
               WHERE company_id=%s""",
            (clean(form["company_name"]), clean(form.get("industry")),
             clean(form.get("website")), clean(form.get("city")),
             clean(form.get("state")), clean(form.get("notes")), company_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Company updated.", "success")
        return redirect(url_for("companies_list"))

    cur.close()
    conn.close()
    return render_template("company_form.html", company=company, action="Edit")


@app.route("/companies/<int:company_id>/delete", methods=["POST"])
def company_delete(company_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # ON DELETE CASCADE removes this company's jobs, contacts, and their applications.
        cur.execute("DELETE FROM companies WHERE company_id = %s", (company_id,))
        conn.commit()
        flash("Company deleted, along with its jobs, contacts, and applications.", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Could not delete company: {err}", "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("companies_list"))


# ---------- JOBS ----------

JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]


def get_companies():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT company_id, company_name FROM companies ORDER BY company_name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def parse_skills(text):
    """Turn 'Python, SQL, Flask' into ['Python', 'SQL', 'Flask'] for storage as JSON."""
    return [s.strip() for s in (text or "").split(",") if s.strip()]


def parse_job_form(form):
    """Validate and clean the job form. Returns (values_tuple, error_message)."""
    if not clean(form.get("company_id")):
        return None, "Please choose a company."
    if not clean(form.get("job_title")):
        return None, "Job title is required."
    smin, smax = clean(form.get("salary_min")), clean(form.get("salary_max"))
    if smin and smax and float(smin) > float(smax):
        return None, "Minimum salary can't be higher than maximum salary."
    skills = parse_skills(form.get("requirements"))
    values = (
        int(form["company_id"]),
        clean(form["job_title"]),
        clean(form.get("job_description")),
        smin, smax,
        clean(form.get("job_type")),
        clean(form.get("posting_url")),
        clean(form.get("date_posted")),
        1 if form.get("is_active") else 0,
        json.dumps(skills),
    )
    return values, None


@app.route("/jobs")
def jobs_list():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT j.job_id, j.job_title, j.job_type, j.salary_min, j.salary_max,
               j.date_posted, j.is_active, j.requirements, c.company_name
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY c.company_name, j.job_title
    """)
    jobs = cur.fetchall()
    cur.close()
    conn.close()
    for job in jobs:
        skills = job["requirements"]
        if isinstance(skills, str):
            skills = json.loads(skills)
        job["skills"] = ", ".join(skills or [])
    return render_template("jobs.html", jobs=jobs)


@app.route("/jobs/add", methods=["GET", "POST"])
def job_add():
    if request.method == "POST":
        form = request.form.to_dict()
        values, error = parse_job_form(form)
        if error:
            flash(error, "error")
            return render_template("job_form.html", job=form, action="Add",
                                   companies=get_companies(), job_types=JOB_TYPES)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jobs (company_id, job_title, job_description, salary_min, salary_max,
                              job_type, posting_url, date_posted, is_active, requirements)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()
        cur.close()
        conn.close()
        flash("Job added.", "success")
        return redirect(url_for("jobs_list"))
    return render_template("job_form.html", job={"is_active": 1}, action="Add",
                           companies=get_companies(), job_types=JOB_TYPES)


@app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
def job_edit(job_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    job = cur.fetchone()
    if job is None:
        cur.close()
        conn.close()
        abort(404)

    if request.method == "POST":
        form = request.form.to_dict()
        values, error = parse_job_form(form)
        if error:
            flash(error, "error")
            cur.close()
            conn.close()
            return render_template("job_form.html", job=form, action="Edit",
                                   companies=get_companies(), job_types=JOB_TYPES)
        cur.execute("""
            UPDATE jobs SET company_id=%s, job_title=%s, job_description=%s, salary_min=%s,
                            salary_max=%s, job_type=%s, posting_url=%s, date_posted=%s,
                            is_active=%s, requirements=%s
            WHERE job_id=%s
        """, values + (job_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash("Job updated.", "success")
        return redirect(url_for("jobs_list"))

    cur.close()
    conn.close()
    job["requirements"] = ", ".join(
        json.loads(job["requirements"]) if isinstance(job["requirements"], str)
        else (job["requirements"] or [])
    )
    return render_template("job_form.html", job=job, action="Edit",
                           companies=get_companies(), job_types=JOB_TYPES)


@app.route("/jobs/<int:job_id>/delete", methods=["POST"])
def job_delete(job_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # ON DELETE CASCADE removes this job's applications too.
        cur.execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
        conn.commit()
        flash("Job deleted, along with its applications.", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Could not delete job: {err}", "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("jobs_list"))


# ---------- APPLICATIONS ----------

STATUS_OPTIONS = ['Applied', 'Phone screen', 'Interview completed',
                  'Offer accepted', 'Rejected', 'Withdrawn']

INSERT_APPLICATION_SQL = """
    INSERT INTO applications
        (job_id, application_date, status, resume_version,
         cover_letter_sent, response_date, interview_date,
         notes, interview_data)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

UPDATE_APPLICATION_SQL = """
    UPDATE applications
    SET job_id = %s, application_date = %s, status = %s,
        resume_version = %s, cover_letter_sent = %s,
        response_date = %s, interview_date = %s,
        notes = %s, interview_data = %s
    WHERE application_id = %s
"""


def _load_jobs(cursor):
    cursor.execute("""
        SELECT j.job_id, j.job_title, c.company_name
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY c.company_name, j.job_title
    """)
    return cursor.fetchall()


def _read_form(form):
    """Validate the application form and return the INSERT/UPDATE parameters.

    Raises ValueError with a message the user can read.
    """
    job_id = clean(form.get("job_id"))
    if not job_id:
        raise ValueError("Please choose a job.")

    application_date = clean(form.get("application_date"))
    if not application_date:
        raise ValueError("Application date is required.")

    status = clean(form.get("status"))
    if status not in STATUS_OPTIONS:
        raise ValueError("Please choose a valid status.")

    raw_interview = clean(form.get("interview_data"))
    if raw_interview:
        try:
            interview_data = json.dumps(json.loads(raw_interview))
        except json.JSONDecodeError:
            raise ValueError("Interview data must be valid JSON.")
    else:
        interview_data = None

    return (
        int(job_id),
        application_date,
        status,
        clean(form.get("resume_version")),
        1 if form.get("cover_letter_sent") else 0,
        clean(form.get("response_date")),
        clean(form.get("interview_date")),
        clean(form.get("notes")),
        interview_data,
    )


def _handle_application_form(application_id=None):
    """Shared handler for the add (application_id=None) and edit forms."""
    action = "Edit" if application_id is not None else "Add"
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = None
    application = None
    try:
        if request.method == "POST":
            try:
                params = _read_form(request.form)
                if application_id is None:
                    cursor.execute(INSERT_APPLICATION_SQL, params)
                else:
                    cursor.execute(UPDATE_APPLICATION_SQL, params + (application_id,))
                conn.commit()
                flash("Application saved.", "success")
                return redirect(url_for("applications"))
            except ValueError as err:
                error = str(err)
            except mysql.connector.Error as err:
                conn.rollback()
                error = f"Database error: {err}"

            # Keep what the user typed so they can correct it.
            application = request.form.to_dict()
            application["cover_letter_sent"] = bool(request.form.get("cover_letter_sent"))

        elif application_id is not None:
            cursor.execute(
                "SELECT * FROM applications WHERE application_id = %s",
                (application_id,),
            )
            application = cursor.fetchone()
            if application is None:
                abort(404)
            application["cover_letter_sent"] = bool(application["cover_letter_sent"])

        jobs = _load_jobs(cursor)
        return render_template(
            "application_form.html",
            application=application,
            application_id=application_id,
            jobs=jobs,
            statuses=STATUS_OPTIONS,
            action=action,
            error=error,
        )
    finally:
        cursor.close()
        conn.close()


@app.route("/applications")
def applications():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
    SELECT a.application_id, a.application_date, a.status, a.resume_version,
           a.cover_letter_sent, a.response_date, a.interview_date, a.notes,
           j.job_title, c.company_name
    FROM applications a
    JOIN jobs j ON a.job_id = j.job_id
    JOIN companies c ON j.company_id = c.company_id
    ORDER BY a.application_date DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("applications.html", applications=rows)


@app.route("/applications/new", methods=["GET", "POST"])
def add_application():
    return _handle_application_form()


@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
def edit_application(application_id):
    return _handle_application_form(application_id)


@app.route("/applications/<int:application_id>/delete", methods=["POST"])
def delete_application(application_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM applications WHERE application_id = %s", (application_id,))
        conn.commit()
        flash("Application deleted.", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Could not delete application: {err}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for("applications"))

# ---------- CONTACTS ----------
def _read_contact_form(form):
    """Validate the contact form. Returns (params, error)."""
    first_name = clean(form.get("first_name"))
    last_name = clean(form.get("last_name"))
    email = clean(form.get("email"))
    linkedin = clean(form.get("linkedin_url"))

    if not first_name or not last_name:
        return None, "First and last name are required."
    if email and "@" not in email:
        return None, "Email doesn't look valid."
    if linkedin and not linkedin.startswith(("https://", "http://")):
        return None, "LinkedIn URL must start with http:// or https://."

    params = (first_name, last_name, email, clean(form.get("phone")),
              clean(form.get("job_title")), linkedin, clean(form.get("notes")))
    return params, None


@app.route("/companies/<int:company_id>/contacts")
def contacts_list(company_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM companies WHERE company_id = %s", (company_id,))
        company = cur.fetchone()
        if company is None:
            abort(404)
        cur.execute(
            """SELECT * FROM contacts
               WHERE company_id = %s
               ORDER BY last_name, first_name""",
            (company_id,),
        )
        contacts = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return render_template("contacts.html", company=company, contacts=contacts)


@app.route("/companies/<int:company_id>/contacts/add", methods=["GET", "POST"])
def contact_add(company_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM companies WHERE company_id = %s", (company_id,))
        company = cur.fetchone()
        if company is None:
            abort(404)

        contact = {}
        if request.method == "POST":
            params, error = _read_contact_form(request.form)
            if error is None:
                cur.execute(
                    """INSERT INTO contacts
                       (company_id, first_name, last_name, email, phone,
                        job_title, linkedin_url, notes)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (company_id, *params),
                )
                conn.commit()
                flash("Contact added.", "success")
                return redirect(url_for("contacts_list", company_id=company_id))
            flash(error, "error")
            contact = request.form
    finally:
        cur.close()
        conn.close()
    return render_template("contact_form.html", company=company, contact=contact,
                           action=url_for("contact_add", company_id=company_id),
                           title="Add contact")


@app.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
def contact_edit(contact_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM contacts WHERE contact_id = %s", (contact_id,))
        contact = cur.fetchone()
        if contact is None:
            abort(404)
        company_id = contact["company_id"]
        cur.execute("SELECT * FROM companies WHERE company_id = %s", (company_id,))
        company = cur.fetchone()

        if request.method == "POST":
            params, error = _read_contact_form(request.form)
            if error is None:
                cur.execute(
                    """UPDATE contacts
                       SET first_name=%s, last_name=%s, email=%s, phone=%s,
                           job_title=%s, linkedin_url=%s, notes=%s
                       WHERE contact_id=%s""",
                    (*params, contact_id),
                )
                conn.commit()
                flash("Contact updated.", "success")
                return redirect(url_for("contacts_list", company_id=company_id))
            flash(error, "error")
            contact = request.form
    finally:
        cur.close()
        conn.close()
    return render_template("contact_form.html", company=company, contact=contact,
                           action=url_for("contact_edit", contact_id=contact_id),
                           title="Edit contact")


@app.route("/contacts/<int:contact_id>/delete", methods=["POST"])
def contact_delete(contact_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT company_id FROM contacts WHERE contact_id = %s", (contact_id,))
        row = cur.fetchone()
        if row is None:
            abort(404)
        company_id = row["company_id"]
        cur.execute("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()
    flash("Contact deleted.", "success")
    return redirect(url_for("contacts_list", company_id=company_id))

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """SELECT
                 (SELECT COUNT(*) FROM applications) AS applications,
                 (SELECT COUNT(*) FROM jobs)         AS jobs,
                 (SELECT COUNT(*) FROM companies)    AS companies,
                 (SELECT COUNT(*) FROM contacts)     AS contacts"""
        )
        totals = cur.fetchone()

        cur.execute("SELECT status, COUNT(*) AS n FROM applications GROUP BY status")
        counts = {row["status"]: row["n"] for row in cur.fetchall()}

        cur.execute(
            """SELECT a.application_date, a.status, j.job_title, c.company_name
               FROM applications a
               JOIN jobs j ON a.job_id = j.job_id
               JOIN companies c ON j.company_id = c.company_id
               ORDER BY a.application_date DESC, a.application_id DESC
               LIMIT 5"""
        )
        recent = cur.fetchall()

        cur.execute("SELECT skill_name FROM user_skills")
        user_skills = [row["skill_name"] for row in cur.fetchall()]

        cur.execute(
            """SELECT j.job_id, j.job_title, j.is_active, j.requirements, c.company_name
               FROM jobs j
               JOIN companies c ON j.company_id = c.company_id"""
        )
        job_rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    total_apps = totals["applications"]
    by_status = []
    for status in STATUS_OPTIONS:
        n = counts.get(status, 0)
        pct = round(n * 100 / total_apps, 1) if total_apps else 0
        by_status.append({"status": status, "n": n, "pct": pct})

    matches = []
    for job in job_rows:
        required = job["requirements"]
        if isinstance(required, str):
            required = json.loads(required)
        percent, missing = calculate_match(user_skills, required or [])
        matches.append({
            "job_title": job["job_title"],
            "company_name": job["company_name"],
            "is_active": bool(job["is_active"]),
            "percent": percent,
            "missing": missing,
        })
    matches.sort(key=lambda m: (m["percent"] is None, -(m["percent"] or 0)))

    return render_template(
        "dashboard.html",
        totals=totals,
        interviews=counts.get("Interview completed", 0),
        offers=counts.get("Offer accepted", 0),
        by_status=by_status,
        recent=recent,
        matches=matches,
    )
# ---------- PROFILE ----------

@app.route("/profile")
def profile():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT skill_name, created_at FROM user_skills ORDER BY skill_name")
        skills = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return render_template("profile.html", skills=skills)


@app.route("/profile/skills/add", methods=["POST"])
def add_skill():
    skill_name = clean(request.form.get("skill_name"))
    if not skill_name:
        flash("Skill name is required.", "error")
        return redirect(url_for("profile"))
    if len(skill_name) > 50:
        flash("Skill name must be 50 characters or fewer.", "error")
        return redirect(url_for("profile"))

    conn = get_connection()
    cur = conn.cursor()
    try:
        # INSERT IGNORE skips duplicates; rowcount tells us whether a row was added.
        cur.execute(
            "INSERT IGNORE INTO user_skills (skill_name) VALUES (%s)",
            (skill_name,),
        )
        conn.commit()
        added = cur.rowcount == 1
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Could not save skill: {err}", "error")
        return redirect(url_for("profile"))
    finally:
        cur.close()
        conn.close()

    if added:
        flash(f"Skill '{skill_name}' added.", "success")
    else:
        flash(f"'{skill_name}' is already in your profile.", "info")
    return redirect(url_for("profile"))


@app.route("/profile/skills/<path:skill_name>/delete", methods=["POST"])
def delete_skill(skill_name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM user_skills WHERE skill_name = %s", (skill_name,))
        conn.commit()
        removed = cur.rowcount == 1
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Could not remove skill: {err}", "error")
        return redirect(url_for("profile"))
    finally:
        cur.close()
        conn.close()

    if removed:
        flash(f"Skill '{skill_name}' removed.", "success")
    else:
        flash(f"Skill '{skill_name}' was not found.", "error")
    return redirect(url_for("profile"))

if __name__ == "__main__":
    app.run(debug=True)
