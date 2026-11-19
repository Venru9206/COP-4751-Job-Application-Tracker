\# AI Usage



This project was built as a learning exercise in Flask and MySQL. It was developed through an iterative collaboration between me (the developer) and AI language models. I made the design decisions, ran and tested every feature, and was responsible for the final code. The AI contributed drafts, explanations, debugging help, and code that I reviewed, modified, or replaced.



\## Division of Work



\- \*\*Developer (me):\*\* Project goals and roadmap, database design decisions, choosing `ON DELETE CASCADE` for foreign keys, testing each feature in the browser, diagnosing bugs, and deciding which AI-generated code to keep, change, or discard.

\- \*\*AI assistant:\*\* Drafting routes, templates, and SQL; explaining errors and suggesting fixes; reviewing code for issues such as unsafe redirects, quoting problems, and input validation gaps; and writing this documentation.

\- \*\*External AI tools:\*\* Generated initial files for the Dashboard, Contacts, and Job Match features. These were reviewed before use, and several parts were replaced.



\## Where AI Was Used



| Area | AI involvement | My changes and verification |

|---|---|---|

| `schema.sql` | Drafted the table definitions from my specification. | Adjusted column types (`company\_ID` renamed to `company\_id`, `job\_type` and `status` changed to ENUM), added a unique key on jobs, and confirmed cascade behavior. |

| Flask skeleton and database connection | Drafted the connection code. | Moved the MySQL password and `FLASK\_SECRET\_KEY` to environment variables. Confirmed the connection works. |

| Companies CRUD | Drafted routes and templates. | Tested add, edit, and delete. |

| Jobs CRUD | Drafted routes and templates. | Removed duplicate entries, added the `uq\_company\_job\_title` key, and tested all operations. |

| Applications CRUD | Drafted routes, the `\_handle\_application\_form` helper, and templates. | Verified JSON validation for `interview\_data`, NULL storage for blank input, flash message styling, and the end-to-end flow. Diagnosed and removed a stray "Companies in database" string. |

| Contacts CRUD | An external AI generated a standalone template. I replaced it with a nested version for `/companies/<company\_id>/contacts`. Routes and the form template were drafted with AI help. | Removed the redundant Company column, replaced the delete confirmation to avoid quoting issues, added LinkedIn URL scheme checks, and tested the flow. |

| Documentation | Drafted this file. | Reviewed for accuracy against the project history. |



\## Verification Practices



\- Every feature was tested in the browser before I accepted it.

\- Database changes were checked directly in MySQL.

\- AI-suggested code was checked for parameterized queries (`%s`), server-side validation, and escaped output.

\- Where AI output conflicted with behavior I observed, I trusted the observed behavior and corrected the code.



\## Known Limitations



\- Some AI-generated code was accepted after review rather than rewritten, so it may reflect patterns I did not personally choose.

\- Browser and server behavior differed during testing (for example, template and route changes needed a server restart), and some troubleshooting was trial and error.



