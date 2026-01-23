
from src.io import FirebaseClient

def get_all_subjects(client:FirebaseClient):
    data = client.get_all_data("programs-display")
    subjects = set()
    for program in data:
        subjects.update(data[program]["overview"]["subject"])
    return list(subjects)

db = FirebaseClient.get_instance()
all_subjects = get_all_subjects(db)

INSTRUCTIONS = {
    "overview": """
You are given a partially filled JSON schema shown after ADD NEWLY FOUND INFORMATION ONTO THIS SCHEMA. Your task is to update only the 'overview' section using information from the text after WEBPAGE CONTENTS START HERE.

If the webpage content does NOT relate to or mention the program described in TARGET PROGRAM INFORMATION, or if the website is unreachable or returns a "page not found" error, return only: {"unrelated_website": true}

Core rules:
- Do NOT infer or guess.
- Only update fields you can confirm directly from the content.
- Leave all other fields exactly as they are: "not provided" or [].
- Do NOT change the structure of the given schema.
- CRITICAL: Return ONLY the overview object WITHOUT wrapping it in an "overview" key.

Expected output format:
{
  "title": "...",
  "provider": "...",
  "description": "...",
  "link": "not provided",
  "favicon": "not provided",
  "subject": [...],
  "tags": [...]
}

Fill:
- "title": Full program name if explicitly given.
- "provider": Organization offering the program.
- "description": A summary or mission statement if present.
- "subject": List of academic topics explicitly stated.
  - It is acceptable for subjects to be derived from hiring skillsets or offered courses
  - If no direct subject can be found, infer at least one subject based on the name or description, or if absolutely not clear, put "various".
- "tags": Keywords like "free", "residential", or "virtual" if explicitly mentioned.

In the schema there may be a "link" key; that is for us only so don't add it.
""",

    "eligibility": """
You are updating the 'eligibility' section of the JSON schema shown after ADD NEWLY FOUND INFORMATION ONTO THIS SCHEMA, using only data from WEBPAGE CONTENTS START HERE.

If the webpage content does NOT relate to or mention the program described in TARGET PROGRAM INFORMATION, or if the website is unreachable or returns a "page not found" error, return only: {"unrelated_website": true}

Core rules:
- Use only explicitly stated information.
- Never infer grade level from age or the reverse.
- Leave all untouched fields as "not provided" or [].
- Do NOT change the structure of the given schema.
- CRITICAL: Return ONLY the eligibility object WITHOUT wrapping it in an "eligibility" key.

Expected output format:
{
  "requirements": {
    "essay_required": ...,
    "recommendation_required": ...,
    "transcript_required": ...,
    "other": [...]
  },
  "eligibility": {
    "grades": [...],
    "age": {
      "minimum": "...",
      "maximum": "..."
    }
  }
}

Fill:
- "essay_required", "recommendation_required", "transcript_required": Use true, false, or "not provided".
- "other": List any extra requirements mentioned like "An interview is required" or "A portfolio is required".
- "grades": Convert phrases like "rising 11th and 12th graders" to "Rising Junior" and "Rising Senior". Don't include "Rising" if not specified.
- "age": Fill "minimum" or "maximum" only if exact numbers are provided.

Be literal and precise — convert 9th, 10th, 11th, and 12th grade to freshman, sophomore, junior, and senior respectively.
""",

    "dates": """
You are updating the 'dates' section of the JSON schema shown after ADD NEWLY FOUND INFORMATION ONTO THIS SCHEMA using content from WEBPAGE CONTENTS START HERE.

If the webpage content does NOT relate to or mention the program described in TARGET PROGRAM INFORMATION, or if the website is unreachable or returns a "page not found" error, return only: {"unrelated_website": true}

Core rules:
- Never infer or estimate.
- Always use mm-dd-yyyy for dates.
- Leave unchanged fields as "not provided".
- Do NOT change the structure of the given schema.
- CRITICAL: Return ONLY the dates object WITHOUT wrapping it in a "dates" key.

Expected output format:
{
  "deadlines": [
    {
      "name": "...",
      "priority": "...",
      "term": "...",
      "date": "...",
      "rolling_basis": ...,
      "time": "..."
    }
  ],
  "dates": [
    {
      "term": "...",
      "start": "...",
      "end": "..."
    }
  ],
  "duration_weeks": ...
}

Update deadlines:
- Add each deadline as a separate object.
- Fields: "name", "priority" ("high" only for the most important application deadline, rank other priorities yourself based on context), "term", "date", "rolling_basis", and "time".

Update program dates:
- Include term (Summer, Winter, Spring, Fall), start, and end dates only if both are clearly stated.
- Use mm-dd-yyyy format.
  - Providing only the month for dates where the days aren't given is acceptable (e.g. "September 2026")
  - If the year isn't provided, it is safe to assume that it refers to the current year

Update duration_weeks:
- Use a number only if the duration is clearly stated (e.g., "6-week program").
- Otherwise "not provided".

Do not infer dates or duration from vague phrases like "a few weeks".
""",

    "locations": """
Update the 'locations' section of the schema shown after ADD NEWLY FOUND INFORMATION ONTO THIS SCHEMA using data from WEBPAGE CONTENTS START HERE.

If the webpage content does NOT relate to or mention the program described in TARGET PROGRAM INFORMATION, or if the website is unreachable or returns a "page not found" error, return only: {"unrelated_website": true}

Core rules:
- Use only explicitly mentioned info.
- Infer locations based on well known campuses carefully with the context.
- Leave untouched fields as "not provided".
- Do NOT change the structure of the given schema.
- CRITICAL: Return ONLY the locations object WITHOUT wrapping it in a "locations" key.

Expected output format:
{
  "locations": [
    {
      "virtual": ...,
      "state": "...",
      "city": "...",
      "address": "..."
    }
  ]
}

Fill:
- "virtual": true if clearly online, false if clearly in-person, "both available" if both are available, "not provided" if unclear.
- "state", "city", "address": Use only if directly stated.

Include only the main residential/instructional site — ignore travel destinations or event locations.
""",

    "costs": """
You are updating the 'costs' section of the schema shown after ADD NEWLY FOUND INFORMATION ONTO THIS SCHEMA using content from WEBPAGE CONTENTS START HERE.

If the webpage content does NOT relate to or mention the program described in TARGET PROGRAM INFORMATION, or if the website is unreachable or returns a "page not found" error, return only: {"unrelated_website": true}

Core rules:
- Use only direct mentions — do not assume or calculate.
- Leave all other values as "not provided" or null.
- Do NOT change the structure of the given schema.
- CRITICAL: Return ONLY the costs object WITHOUT wrapping it in a "costs" key.

Expected output format:
{
  "costs": [
    {
      "name": "...",
      "free": ...,
      "lowest": ...,
      "highest": ...,
      "financial_aid_available": ...
    }
  ],
  "stipend": {
    "available": ...,
    "amount": ...
  }
}

Cost objects (tuition, fees, etc.):
- "free": Set to true only if explicitly stated. If true, set "lowest" and "highest" to null.
- "lowest"/"highest": Use numbers only if directly stated; if not stated and not free, leave as "not provided".
- "financial_aid_available": true, false, or "not provided".

Stipend:
- "available": true only if explicitly mentioned, false if clearly absent, "not provided" if unclear.
- "amount": Use numeric value only if stated. If "available" is false, set amount to null.
  - If rate is given, for example hourly or per session, write the amount and the rate (eg. 16.50 per hour, 200 per week, 100 per session)
  - If the amount for the entire program can be calculated explicitly given the rate and amount of sessions, calculate that and return it (eg. 100 per session, 7 sessions -> 700)

Include each cost type as a separate object if multiple are mentioned.
Also keep in mind that some websites offer a variety of internships as one single internship. If multiple internships are found, assume that this is the case and have the lowest cost be the price of the internship with the lowest cost and the highest cost be the price of the internship with the highest cost.
""",

    "contact": """
Update the 'contact' section of the schema shown after ADD NEWLY FOUND INFORMATION ONTO THIS SCHEMA using data found in WEBPAGE CONTENTS START HERE.

If the webpage content does NOT relate to or mention the program described in TARGET PROGRAM INFORMATION, or if the website is unreachable or returns a "page not found" error, return only: {"unrelated_website": true}

Core rules:
- Only include contact info shown directly in the webpage content.
- Do not infer or assume from context or page layout.
- Leave fields as "not provided" if missing.
- Only include the most important contact to an applicant.
- CRITICAL: Return ONLY the contact object WITHOUT wrapping it in a "contact" key.

Expected output format:
{
  "contact": {
    "email": "...",
    "phone": "..."
  }
}

Fill:
- "email": Must be a complete email address found directly in the content.
- "phone": Must be clearly formatted and complete (123-456-7890).

Do not copy from social links or headers unless the contact is fully visible in the content. 
""",

    "all": """
You are given a partially filled JSON schema after the line: ADD NEWLY FOUND INFORMATION ONTO THIS SCHEMA. 
Extract structured data from the HTML/plaintext that follows WEBPAGE CONTENTS START HERE and update the JSON schema accordingly.

If the webpage content does NOT relate to or mention the program described in TARGET PROGRAM INFORMATION, or if the website is unreachable or returns a "page not found" error, return only:
{"unrelated_website": true}

—————
GLOBAL RULES:
- Do NOT add or remove any keys from the schema.
- Do NOT infer, guess, or hallucinate information.
- Use "not provided" for missing text fields or categories.
- Use mm-dd-yyyy for all dates or just the year, or month and year if that is the only information given.
- Only update values that are explicitly supported by the provided text.
- Do not change or overwrite any field that already contains data unless new text confirms a change or addition.
- Do not include any rationale or explanation in the output—just structured values.

—————
SECTION INSTRUCTIONS:

1. OVERVIEW:
- "title": Use the full program name only if explicitly stated.
- "provider": The organization running the program.
- "description": A concise summary, directly quoted or reworded from mission/program overview.
- "link": A direct URL to the program or application if provided.
- "subject": List stated academic topics (e.g., biology, computer science).
  - It is acceptable for subjects to be derived from hiring skillsets or offered courses
  - If no direct subject can be found, infer at least one subject based on the name or description, or if absolutely not clear, put "various".
- "tags": Use literal keywords (e.g., "free", "residential", "virtual", etc.).

Below are a list of subjects that currently exist in our database:\n"""
+str(all_subjects)+"""\n
If the program subjects fall under any of the following subjects, label it with those specific subjects instead no matter what specific wording the program uses.
For example if the program has subject "AI", since "Artifical Intelligence" is already an existent subject, label it with "Artificial Intelligence" instead.
The same goes for "Arts" and "Art". Use "Art" instead.

2. ELIGIBILITY:
- "essay_required", "recommendation_required", "transcript_required": Use true, false, or "not provided".
- "other": List any extra requirements (e.g., "An interview is required").
- "grades": Convert stated grades (e.g., 11th) into ["Junior"], and use "Rising" only if explicitly stated (e.g., "Rising Seniors").
- "age": Fill "minimum" and "maximum" with numeric values only if exact ages or age ranges are given.

Never infer age from grade or vice versa.

3. DATES:
- "deadlines": For each deadline found, fill all subfields:
  - "name" (e.g., "Priority Deadline", "Final Application Deadline")
  - "priority" ("high" only for the most important application deadline, "medium"/"low" for others)
  - "term", "date", "rolling_basis", and "time" — use "not provided" if not stated.
- "dates": Include program term, start, and end dates only if both dates are provided. Leave subfields as "not provided" if only partial data is available.
  - Providing only the month for dates where the days aren't given is acceptable (e.g. "September 2026")
  - If the year isn't provided, it is safe to assume that it refers to the current year
- "duration_weeks": Use a number only if clearly stated (e.g., "6-week program" → 6); otherwise "not provided".

Never derive exact duration from vague phrases like "a few weeks".

4. LOCATIONS:
- "virtual": Use:
  - true — if the program is explicitly online only
  - false — if explicitly in-person
  - "both available" — if users can choose between online or in-person or if the program is hybrid
  - "not provided" — if unclear
- "state", "city", "address": Only fill if explicitly stated in the text.

Do not infer the location based on provider, university, or assumptions.

5. COSTS:
Each cost-related item gets its own object (never leave the costs list empty, if it explicitly says there are no costs, just put "free" as true without removing the object from the list):
- "name": Label of the cost (e.g., Tuition, Housing).
- "free": true only if clearly stated. If true, both "lowest" and "highest" must be null.
- "lowest" / "highest": Use only numeric values if explicitly stated (e.g., $2500). Else use "not provided".
- "financial_aid_available": true, false, or "not provided".

Stipend:
- "available": true if explicitly mentioned; false if explicitly absent; "not provided" if unclear.
- "amount": Use numeric value only if stated. If "available" is false, set amount to null.

Never calculate cost or stipend from scattered clues.

6. CONTACT:
Include only the most relevant applicant-facing contact info:
- "email": Must be a complete email address found directly in the content.
- "phone": Must be a valid phone number with format (e.g., 123-456-7890).
- If not explicitly present, use "not provided".

Never extract contact info from headers, footers, or social links unless it appears clearly in main content.

—————
FINAL NOTE:
Return only the updated JSON. Never explain your reasoning. Preserve the schema structure. Only change fields if the corresponding information appears in the provided text.

For any website that is unreachable, missing, or returns a "page not found" error (or any HTTP 4xx/5xx error), treat it as an unrelated website and return: {"unrelated_website": true}.
""",

    "evaluate_links": """
You are given a dictionary after the line: QUEUE HERE.
You are also given a partially filled JSON schema after PROGRAM INFO.
The dictionary represents a queue to go through links for web crawling purposes needed to find information to completely fill the partially filled JSON schema.
Your job is to go through the the link contents (key) and the URLs (value) and remove all the links that likely wouldn't contain the needed information.

Core rules:
- If a link looks like it points to the admissions for a university, and not the program, it can be removed.
- If a link leads to any links similar to a:
  1. Google Drive
  2. Video (Youtube, Vimeo, etc.)
  3. PDF
  4. Completely unrelated website (unless it is a Google Form)
  It can be removed.
- If a website is unreachable, missing, or returns a "page not found" error, remove it from the queue.

Don't add any links and be very conservative with the link removing process. 
Don't be afraid to remove every link from the queue if it's obvious none of them are needed, in that case return an empty dictionary.
"""
}
