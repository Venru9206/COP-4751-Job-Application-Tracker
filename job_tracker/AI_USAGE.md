# AI Usage Documentation


## Summary

I used generative AI at every stage of this project: planning, schema work, writing and debugging code, testing, and writing the documentation. This project was built as a learning exercise in Flask and MySQL, developed through an iterative collaboration between me and AI language models. I made the design decisions, ran and tested every feature in the browser, and am responsible for the final code. The AI contributed drafts, explanations, debugging help, and code that I reviewed, modified, or replaced.

## Tools Used

- **Claude (Claude Haiku 5.5)**: planning the project steps, starter code for the database connection, the Flask app, and the Companies CRUD routes and templates, and troubleshooting setup errors.
- **Claude (Claude Sonnet 5.5)**: a later session in which I shared my `app.py`, `base.html`, `database.py`, and schema so it could draft the Contacts CRUD, Dashboard, Job Match, CSS, README, and this documentation. It also generated initial files for the Dashboard, Contacts, and Job Match features. I reviewed these before use, and several parts were replaced.
- **Duck.ai (Claude Haiku 5.5)**: project planning, the Jobs and Applications routes and forms, and clearing the duplicate job rows.

## Division of Work

- **Me:** the project goals and roadmap, the database design decisions (including choosing `ON DELETE CASCADE` for foreign keys), testing each feature in the browser, diagnosing bugs, and deciding which AI-generated code to keep, change, or discard.
- **AI assistants:** drafting routes, templates, CSS, and SQL; explaining errors and suggesting fixes; reviewing code for issues such as unsafe redirects, quoting problems, and input validation gaps; and drafting the README and this document.

## Key Prompts

The first six are quoted from my notes. The rest are paraphrased from my chat history, so I may not have used the exact wording.

1. "Walk me through the remaining steps of this project based on the spec" (with the spec pasted in).
2. "What terminal do I put the mysqldump command into? I get 'mysqldump is not recognized.'"
3. "Let's change status to an ENUM and make company_ID lowercase."
4. "I got an access denied error when exporting my schema. How do I fix it?"
5. "Write Companies CRUD routes and templates using my schema (company_id, parameterized queries, delete confirmation)."
6. "I get 'Access denied for user root (using password: NO)' when running app.py. What's wrong?"
7. "The project is due today and my database already has all four tables filled in. What is the first step?"
8. "Why does each job appear three times, and is it safe to delete the extra rows?"
9. "Write the Applications add, edit, and delete routes with a job dropdown and a status dropdown."
10. "Why is my /applications page not showing anything?"
11. "Here is my app.py, base.html, schema, and database.py. Write Contacts CRUD, the Dashboard, and Job Match using my actual column names."
12. "Help me finish the project: fix formatting, write the README and AI_USAGE.md, push to GitHub, and check the requirements."

## Where AI Was Used

| Area | AI involvement | My changes and verification |
|---|---|---|
| `schema.sql` | Drafted the table definitions from my specification and explained how to export them. | Used the MySQL Workbench export after the command-line export was blocked by an access error. Adjusted column types (`company_ID` renamed to `company_id`, `job_type` and `status` changed to ENUM), added a unique key on jobs, and confirmed cascade behavior. |
| Flask skeleton and database connection | Drafted the connection code. | Moved the MySQL password and `FLASK_SECRET_KEY` to environment variables. Confirmed the connection works. |
| Companies CRUD | Drafted routes and templates. | Tested add, edit, and delete. |
| Jobs CRUD | Drafted routes and templates. | Removed the duplicate entries, added the `uq_company_job_title` key, and tested all operations. |
| Applications CRUD | Drafted routes, the `_handle_application_form` helper, and templates. | Verified JSON validation for `interview_data`, NULL storage for blank input, flash message styling, and the end-to-end flow. Diagnosed and removed a stray "Companies in database" string. |
| Contacts CRUD | Claude generated a standalone template. It also drafted routes and templates against my schema. I replaced the standalone template with a nested version for `/companies/<company_id>/contacts`. | Removed the redundant Company column, replaced the delete confirmation to avoid quoting issues, added LinkedIn URL scheme checks, and tested the flow. |
| Dashboard and Job Match | Drafted the dashboard queries, the Job Match scoring function (matched skills / required skills × 100, ignoring case and extra spaces), and their templates. | Mapped the dashboard's "interviews" and "offers" to my own status values and tested both against my data. Job Match was checked against the spec's Python, SQL, Flask example. |
| CSS and layout | Drafted `style.css` and the updated `base.html`. | Fixed formatting issues I found while testing. The checkbox for the active job status was misaligned, and some of the buttons were too close to their text boxes. |
| Documentation | Drafted the README and this file. | Reviewed both for accuracy against the project history. |

## What Worked Well

- The step-by-step plan broke the spec into phases that matched the course timeline.
- Troubleshooting was quick when I pasted the exact error message. Error text was the most useful input.
- Starter code for the database connection and Companies CRUD followed a consistent pattern, including one shared handler for the add and edit forms, that I could copy for the other tables.
- Using environment variables for the database password and secret key kept credentials out of the code, and parameterized queries were used throughout.
- A safe plan for removing the duplicate jobs: back up first, check whether any applications referenced the duplicates, then delete and verify.

## What I Changed

- Changed the password handling from a hardcoded value to an environment variable, so it wouldn't be committed to GitHub, and loaded `FLASK_SECRET_KEY` from the environment too.
- Adapted the schema to match my existing database: renamed `company_ID` to `company_id`, and changed `status` and `job_type` to ENUMs with values that matched my data.
- Kept my original status values ("Phone screen", "Interview completed", "Offer accepted") instead of renaming them, and added "Rejected" and "Withdrawn".
- Cleaned up the duplicate job rows (30 rows down to 10) and added a unique key to prevent them coming back.
- Switched the foreign keys to `ON DELETE CASCADE` and updated the delete routes and messages to say what gets removed.
- Removed duplicated code blocks from `app.py`.
- Adjusted AI-written code to my real schema: `first_name` and `last_name` instead of `contact_name`, `posting_url` instead of `job_url`, and my own status values.
- Added validation the AI first omitted, such as the salary range check, JSON checks, and email and URL checks.
- Restructured Contacts to be nested under companies, and replaced the delete confirmation to avoid quoting problems.

## Verification Practices

- Every feature was tested in the browser before I accepted it.
- Database changes were checked directly in MySQL.
- AI-suggested code was checked for parameterized queries (`%s`), server-side validation, and escaped output.
- Where AI output conflicted with behavior I observed, I trusted the observed behavior and corrected the code.
- I backed up the database before running AI-suggested DELETE statements.

## Lessons Learned

- Always test AI-generated code by running it. Starter code worked after small fixes, such as matching column names to my actual schema.
- Check the AI's assumptions about your setup, such as file locations, column names, and whether a tool is on your PATH. Several errors came from these, and AI often assumed the spec's schema instead of mine.
- Environment variables only last for the terminal window where they're set. This caused the "using password: NO" error.
- A missing template or nav link made a working page look broken.
- Back up the database before running any AI-suggested DELETE or UPDATE.
- Asking for an explanation of an error helps more than just getting the fix, because I can recognize the problem next time.
- Keeping a running log of prompts and summaries made this document much easier to write.

## Known Limitations

- Some AI-generated code was accepted after review rather than rewritten, so it may reflect patterns I did not personally choose.
- Browser and server behavior differed during testing (for example, template and route changes needed a server restart), and some troubleshooting was trial and error.
- Multiple AI tools worked on different parts of the project, so the coding style is not perfectly uniform.
