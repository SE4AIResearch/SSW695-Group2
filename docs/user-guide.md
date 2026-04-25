# Buma User Guide

A step-by-step guide for first-time users: clone, configure, install, and use Buma.

> **Demo video:** Watch a full walkthrough of Buma in action:
> https://stevens.zoom.us/rec/share/DpeGj3KoGgIkXlwmR3SSpuH__39eKzjHtn9kkbzFWN42T6k-wy4XPu1xdiyueV37.emvdavdLR5sSbDlY?startTime=1776824419000

---

## What is Buma?

Buma is an **Intelligent Bug Triaging & Assignment System** for GitHub repositories. When a new issue is opened in a connected repository, Buma automatically:

1. Validates and ingests the GitHub webhook event
2. Classifies the issue (bug vs. not-a-bug, priority level)
3. Selects the best-fit developer based on team skills and current workload
4. Applies a label, sets the assignee, and posts an explanation comment — directly on the GitHub issue
5. Records every decision in a searchable audit log

The web dashboard lets you configure repositories, manage developer profiles, and inspect triage history.

---

## Prerequisites

Before you begin, make sure you have the following installed:

| Tool | Why you need it | Install |
|---|---|---|
| **Git** | Clone the repository | [git-scm.com](https://git-scm.com) |
| **Docker** + **Docker Compose** | Run the full stack | [docs.docker.com](https://docs.docker.com/get-docker/) |
| **Node.js 18+** | Run the web dashboard (development) | [nodejs.org](https://nodejs.org) |
| A **GitHub account** | Set up the GitHub App and OAuth App | — |

> **Note:** Python and `uv` are only needed if you want to run the backend directly on your machine instead of Docker. The Docker path (recommended) does not require them.

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/SE4AIResearch/SSW695-Group2.git
cd SSW695-Group2
```

---

## Step 2 — Create a GitHub App

Buma needs a **GitHub App** to receive webhook events from your repositories and to write back to issues (labels, assignees, comments).

### 2a. Register the App

1. Go to your GitHub profile → **Settings** → **Developer settings** → **GitHub Apps** → **New GitHub App**.
2. Fill in the form:
   - **GitHub App name:** anything unique (e.g. `buma-yourname`)
   - **Homepage URL:** `http://localhost:8000` (or your public URL)
   - **Webhook URL:** `http://localhost:8000/webhook/github` *(update this later once you have a public URL — see the ngrok note below)*
   - **Webhook secret:** generate a strong random string and copy it — you will paste it into `.env` as `GITHUB_WEBHOOK_SECRET`
3. Under **Permissions**, grant:
   - **Issues** → Read & Write
   - **Metadata** → Read-only
4. Under **Subscribe to events**, check **Issues**.
5. Click **Create GitHub App**.

### 2b. Generate a Private Key

On your new App's settings page, scroll to **Private keys** and click **Generate a private key**. A `.pem` file will be downloaded — keep it safe.

### 2c. Note Your App ID

At the top of the App settings page you will see **App ID** — copy this number.

---

## Step 3 — Create a GitHub OAuth App

The dashboard login uses GitHub OAuth. You need a separate **OAuth App** for this.

1. Go to **Settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**.
2. Fill in:
   - **Application name:** `buma-dashboard` (or anything)
   - **Homepage URL:** `http://localhost:3000`
   - **Authorization callback URL:** `http://localhost:8000/auth/callback`
3. Click **Register application**.
4. On the next page, click **Generate a new client secret**.
5. Copy both the **Client ID** and **Client Secret**.

---

## Step 4 — Configure the Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` in a text editor and fill in every value:

```bash
# Postgres credentials — leave these as-is unless you have a reason to change them
POSTGRES_USER=buma
POSTGRES_PASSWORD=buma
POSTGRES_DB=buma

# Connection strings — use Docker service names (do not change "db" or "redis")
DATABASE_URL=postgresql+psycopg://buma:buma@db:5432/buma
REDIS_URL=redis://redis:6379/0

# GitHub App (from Step 2)
GITHUB_WEBHOOK_SECRET=<the secret you generated in Step 2a>
GITHUB_APP_ID=<your App ID from Step 2c>
GITHUB_APP_PRIVATE_KEY=<contents of the .pem file, with newlines replaced by \n>

# GitHub OAuth App (from Step 3)
GITHUB_OAUTH_CLIENT_ID=<Client ID from Step 3>
GITHUB_OAUTH_CLIENT_SECRET=<Client Secret from Step 3>

# Session security — change this to any long random string
SESSION_SECRET=change-me-to-a-random-string

# CORS — allowed origins for the dashboard
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### How to format the private key

The `.pem` file has multiple lines. You need to put it on a single line with `\n` between each line:

```bash
# On Linux / macOS:
GITHUB_APP_PRIVATE_KEY="$(cat /path/to/your-app.pem | awk '{printf "%s\\n", $0}')"
```

Or open the file, copy all the text, and manually replace every newline with `\n`.

---

## Step 5 — Build and Start the Stack

```bash
docker compose build
docker compose up
```

Docker Compose starts the services in the correct order:

1. **Postgres** and **Redis** start and run health checks
2. **migrate** applies the database schema and exits
3. **gateway** (API, port 8000) and **worker** start

You should see output like:

```
gateway-1  | INFO:     Application startup complete.
worker-1   | [worker] polling buma:triage:queue …
```

Leave this terminal running, or run detached with `docker compose up -d`.

### Verify the gateway is healthy

```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"buma"}
```

---

## Step 6 — Start the Dashboard

The dashboard is a React app. Open a new terminal:

```bash
cd web-dashboard
npm install
npm start
```

The dashboard opens at **http://localhost:3000**.

---

## Step 7 — Log In

1. Open http://localhost:3000 in your browser.
2. Click **Sign in with GitHub**.
3. Authorize the OAuth App you created in Step 3.
4. You will be redirected back to the dashboard, now logged in.

---

## Step 8 — Enroll a Repository

Before Buma will triage issues, you must enroll the repository and define its developer team.

### Via the Dashboard

1. In the sidebar, click **Configuration**.
2. Click **Add Repository**.
3. Enter the repository's full name (e.g. `myorg/myrepo`) and any initial settings.
4. Click **Save**.

### Via the API (curl)

```bash
curl -X POST http://localhost:8000/api/config/repos \
  -H "Content-Type: application/json" \
  -b "<your session cookie>" \
  -d '{
    "repo_full_name": "myorg/myrepo",
    "config": {}
  }'
```

> All `/api/*` routes require you to be logged in. Pass the session cookie from the browser, or use the dashboard UI.

---

## Step 9 — Add Developer Profiles

Buma uses developer profiles to choose assignees. Each profile records skills and current workload capacity.

### Via the Dashboard

1. Open the **Configuration** page for your repository.
2. Click **Add Developer**.
3. Fill in the GitHub login, skills (comma-separated tags), and capacity (a number — higher = more available).
4. Click **Save**.

### Via the API (curl)

```bash
curl -X POST http://localhost:8000/api/config/repos/<repo_id>/developers \
  -H "Content-Type: application/json" \
  -b "<session cookie>" \
  -d '{
    "login": "octocat",
    "skills": ["python", "backend", "auth"],
    "capacity": 5
  }'
```

---

## Step 10 — Expose Buma Publicly with ngrok

GitHub cannot reach `localhost`, so you need a public HTTPS URL that tunnels to your local gateway on port 8000. **ngrok** creates this tunnel for you.

### 10a. Create a free ngrok account

1. Go to https://ngrok.com and click **Sign up** (free plan is enough).
2. Verify your email and log in to the ngrok dashboard.

### 10b. Install ngrok

**macOS (Homebrew):**
```bash
brew install ngrok/ngrok/ngrok
```

**Linux:**
```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok
```

**Windows:** Download the installer from https://ngrok.com/download and run it.

### 10c. Authenticate ngrok with your account

1. In the ngrok dashboard, go to **Your Authtoken** (left sidebar).
2. Copy the token shown.
3. Run this command, replacing `<token>` with your copied token:

```bash
ngrok config add-authtoken <token>
```

You only need to do this once per machine.

### 10d. (Optional but recommended) Claim a static domain

On the free plan, ngrok gives you a random URL every time you start a tunnel. A **static domain** lets you reuse the same URL — you only need to update your GitHub App webhook URL once.

1. In the ngrok dashboard, go to **Cloud Edge** → **Domains** → **New Domain**.
2. ngrok will generate a free static domain like `your-slug.ngrok-free.app` — copy it.

### 10e. Start the tunnel

Open a **new terminal** (leave the Docker stack running in another terminal).

**With a static domain (recommended):**
```bash
ngrok http --domain=your-slug.ngrok-free.app 8000
```

**Without a static domain:**
```bash
ngrok http 8000
```

ngrok will display output like:

```
Forwarding   https://your-slug.ngrok-free.app -> http://localhost:8000
```

Copy the `https://...` URL — this is your public gateway address.

> **Keep ngrok running** the entire time you want Buma to receive webhook events. If you stop ngrok and restart it without a static domain, you will get a new URL and must update your GitHub App settings again.

### 10f. Update the GitHub App webhook URL

1. Go to your GitHub App settings page.
2. Under **Webhook URL**, enter:
   ```
   https://your-slug.ngrok-free.app/webhook/github
   ```
3. Click **Save changes**.

### 10g. Install the App on your repository

1. On your GitHub App settings page, click **Install App** in the left sidebar.
2. Select your GitHub account or organization.
3. Choose **Only select repositories**, pick the repository you enrolled in Step 8, and click **Install**.

### 10h. Verify the webhook is connected

1. On your GitHub App settings page, click **Advanced** → **Recent Deliveries**.
2. You should see a `ping` delivery with a green checkmark — this confirms GitHub can reach your gateway.

---

## Using Buma

Once the stack is running, the app enrolled, and the webhook registered, Buma works automatically.

### Open a test issue

1. Go to your GitHub repository.
2. Click **Issues** → **New issue**.
3. Write a title that describes a bug (e.g. *"Login button crashes on mobile"*) and submit.

Within seconds, Buma will:

- Receive the webhook event
- Classify the issue as a bug and set a priority
- Select a developer from the enrolled team
- Apply a label (e.g. `priority:high`) and set the assignee
- Post a comment explaining the decision

### View triage history

In the dashboard, click **Triage History** in the sidebar. You will see a paginated list of every triage decision, including the assigned developer, priority, and the explanation that was posted as a comment.

### View developer workload

Click **Developer Workload** to see how many open assignments each developer currently has.

---

## API Reference (summary)

| Method | Route | Description |
|---|---|---|
| `GET` | `/health` | Liveness check (no auth required) |
| `POST` | `/webhook/github` | GitHub webhook receiver (no auth — HMAC-verified) |
| `GET` | `/auth/github` | Start OAuth login |
| `GET` | `/auth/callback` | OAuth callback |
| `POST` | `/api/config/repos` | Enroll a repository |
| `GET` | `/api/config/repos/{repo_id}` | Get repo config |
| `PATCH` | `/api/config/repos/{repo_id}` | Update repo config |
| `POST` | `/api/config/repos/{repo_id}/developers` | Add a developer profile |
| `PATCH` | `/api/config/repos/{repo_id}/developers/{login}` | Update a developer profile |
| `DELETE` | `/api/config/repos/{repo_id}/developers/{login}` | Remove a developer profile |
| `GET` | `/api/triage/{repo_id}` | Triage decision history (paginated) |
| `GET` | `/api/workload/{repo_id}` | Developer workload view |

All `/api/*` routes require a valid session cookie (GitHub OAuth login).

Interactive API docs are available at **http://localhost:8000/docs** while the gateway is running.

---

## Stopping the Stack

```bash
# Stop all containers (data is preserved):
docker compose down

# Stop and wipe all data (fresh start):
docker compose down -v
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `migrate` service exits with an error | Database not yet ready | Re-run `docker compose up` — healthchecks should prevent this |
| Gateway returns 401 on `/api/*` | Not logged in | Visit `http://localhost:8000/auth/github` and log in |
| Issues are not being triaged | Repo not enrolled or webhook not registered | Check Steps 8 and 10 |
| Webhook deliveries show red X in GitHub | ngrok not running or wrong URL | Restart ngrok (Step 10e) and confirm the URL in your GitHub App settings matches |
| ngrok URL changes every restart | No static domain claimed | Claim a free static domain (Step 10d) |
| Issues triaged but no label/assignee on GitHub | GitHub App not installed on the repo | Install the App (Step 10) |
| Worker logs show `patch_state=FAILED_RETRY` | GitHub App credentials missing or wrong | Check `GITHUB_APP_ID` and `GITHUB_APP_PRIVATE_KEY` in `.env` |
| Dashboard shows "Network Error" | Gateway not running or CORS mismatch | Confirm gateway is up (`curl localhost:8000/health`) and `CORS_ORIGINS` includes `http://localhost:3000` |

---

## Glossary

| Term | Meaning |
|---|---|
| **GitHub App** | The entity Buma uses to receive webhooks and write back to GitHub issues |
| **OAuth App** | Used for dashboard login (GitHub OAuth 2.0) |
| **Enrolled repository** | A repo Buma is configured to triage (must be done via the dashboard or API) |
| **Developer profile** | A record of a developer's skills and capacity, used for assignee selection |
| **Triage decision** | The output of the triage pipeline: category, priority, assignee, and explanation |
| **DLQ (Dead-Letter Queue)** | Events that failed all processing attempts — visible in the `dlq_records` table |
