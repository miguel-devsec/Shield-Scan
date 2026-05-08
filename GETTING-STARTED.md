# Getting Started with ShieldScan

This guide will walk you through running ShieldScan on your own computer using Docker. You do not need any programming knowledge — just follow the steps in order.

**What you will need:**
- A computer running Windows, macOS, or Linux
- An internet connection (for the first-time setup)
- About 10–15 minutes

---

## Step 1 — Install Docker Desktop

Docker Desktop is a free application that lets your computer run self-contained software packages called **containers**. It is the only thing you need to install — everything else (the database, the web server, the application itself) runs automatically inside containers.

1. Go to [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) and download the version for your operating system.
2. Run the installer and follow the on-screen instructions.
3. Once installed, launch Docker Desktop. You will see a **whale icon** in your taskbar (Windows) or menu bar (Mac) when it is running.

> **Windows users:** During installation, Docker may ask you to enable **WSL 2** (Windows Subsystem for Linux). Click Accept and restart your computer if prompted. This is normal and required.

Do not continue to Step 2 until the Docker Desktop whale icon appears and shows **"Docker is running"**.

---

## Step 2 — Get the project files

You need a copy of the ShieldScan files on your computer. Choose one of the two options below:

### Option A — Using Git (if you have it installed)

Open a terminal (PowerShell on Windows, Terminal on Mac/Linux) and run:

```bash
git clone https://github.com/miguel-devsec/ShieldScan.git
cd ShieldScan
```

### Option B — Download as a ZIP file (no Git required)

1. Go to [https://github.com/miguel-devsec/ShieldScan](https://github.com/miguel-devsec/ShieldScan)
2. Click the green **"Code"** button near the top right
3. Click **"Download ZIP"**
4. Once downloaded, extract (unzip) the folder anywhere on your computer
5. Open a terminal and navigate into the extracted folder:

```bash
# Example — adjust the path to where you extracted it
cd Downloads/ShieldScan-main
```

---

## Step 3 — Create the configuration file

The application needs a small configuration file (called `.env`) that contains a password and a secret key. A ready-to-use template is already included in the project.

**On Windows (PowerShell):**
```powershell
Copy-Item env.example .env
```

**On Mac or Linux:**
```bash
cp env.example .env
```

You do not need to edit this file. The default values are safe for running the application on your own machine.

---

## Step 4 — Start the application

In your terminal, make sure you are still inside the ShieldScan folder, then run:

```bash
docker compose up --build
```

Docker will now download all the necessary components and start the application. **The first time this runs it may take 5–10 minutes** depending on your internet speed — this is normal. Subsequent starts will be much faster.

You will see a lot of output scrolling through the terminal. This is expected. The application is ready when the output slows down and you see repeated status messages from services like `api`, `worker`, and `frontend`.

---

## Step 5 — Open ShieldScan in your browser

Once the application is running, open your web browser and go to:

```
http://localhost:3000
```

You should see the ShieldScan welcome page.

![ShieldScan welcome page](images/creating_account.png)

---

## Step 6 — Create your account

Click **Register** and fill in the form:

| Field | What to enter |
|-------|--------------|
| **Email** | Any email address (does not need to be real for local use) |
| **Password** | Any password with at least 8 characters |

Click **Create Account**. You will be redirected to the login page.

![Registration form](images/creating_account.png)

---

## Step 7 — Log in and run your first audit

1. Enter your email and password, then click **Sign In**
2. You will land on the **Dashboard**
3. Click **New Audit**, enter any website URL (for example `https://example.com`), and click **Start Audit**
4. The audit runs in the background — the page will update automatically when the results are ready

![Dashboard](images/new_user_dashboard.png)

![Running a new audit](images/new_scanning.png)

![Audit results](images/scanning_results.png)

---

## Step 8 — Stop the application when you are done

Go back to the terminal where the application is running and press **Ctrl + C** to stop it. Then run:

```bash
docker compose down
```

This cleanly shuts down all containers. Your data (registered accounts and audit history) is saved and will be available next time you start the application.

---

## Restarting the application later

Once the setup is complete, you only need two commands to start and stop ShieldScan in the future:

**Start:**
```bash
docker compose up -d
```
*(The `-d` flag runs it in the background so your terminal stays free)*

**Stop:**
```bash
docker compose down
```

---

## Troubleshooting

### "Port is already in use" error

Another application on your computer is using port 3000 or 8000. The simplest fix is to stop the conflicting application, then try again.

### The browser shows "This site can't be reached"

Docker is probably still starting up. Wait 30 seconds and refresh the page.

### "Docker is not running" error in the terminal

Open Docker Desktop and wait for the whale icon to show **"Docker is running"**, then try again.

### Containers keep restarting

Run the following command to see error messages:
```bash
docker compose logs
```
Copy the error text and search for it online, or open an issue on the project's GitHub page.

---

## Optional — Enable the monitoring dashboard

ShieldScan includes an optional monitoring stack (Prometheus + Grafana) to observe how the application is performing. To enable it:

```bash
docker compose --profile monitoring up -d
```

| URL | Tool | Default credentials |
|-----|------|-------------------|
| http://localhost:9090 | Prometheus | None required |
| http://localhost:3001 | Grafana | admin / admin |

---

## Need help?

Open an issue on GitHub: [https://github.com/miguel-devsec/ShieldScan/issues](https://github.com/miguel-devsec/ShieldScan/issues)
