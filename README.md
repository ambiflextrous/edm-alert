*Read this in [Português](README.pt.md).*

# EDM Cabo Delgado Power Cut Alerts

Emails you whenever EDM posts a new scheduled power cut ("Corte Programado") for **Cabo Delgado** on https://www.edm.co.mz/manutencao.

Runs for free on GitHub Actions, every 4 hours. It remembers which outage reference codes (e.g. `PEM260705-0092`) it already alerted on, so you only get one email per outage.

## Setup (about 10 minutes)

### 1. Create a Gmail App Password
You need a Gmail account to *send* the alert (it can email any address, including itself).

1. Go to https://myaccount.google.com/security and enable **2-Step Verification** if not already on.
2. Go to https://myaccount.google.com/apppasswords
3. Create an app password named "EDM alert" and copy the 16-character code.

### 2. Create the GitHub repository
1. Sign in to https://github.com (free account is fine).
2. Create a **private** repository, e.g. `edm-alert`.
3. Upload these files keeping the folder structure:
   - `check_edm.py`
   - `README.md`
   - `.github/workflows/edm-alert.yml`

   Easiest way: on the repo page, **Add file → Upload files**, and drag the whole folder contents in. (To create the `.github/workflows` folder via the web UI, use **Add file → Create new file** and type `.github/workflows/edm-alert.yml` as the filename, then paste the workflow content.)

### 3. Add your secrets
In the repo: **Settings → Secrets and variables → Actions → New repository secret**. Add three:

| Name | Value |
|---|---|
| `SMTP_USER` | your Gmail address |
| `SMTP_PASS` | the 16-character app password |
| `ALERT_TO` | the email where you want alerts |

### 4. Test it
Go to the **Actions** tab → "EDM Cabo Delgado outage alert" → **Run workflow**. Since the current Cabo Delgado outage is new to the script, you should receive an email within a minute or two.

## Notes
- To monitor a different province, add a repository secret or edit the script's `PROVINCE` default.
- To change frequency, edit the `cron` line in the workflow (`0 */2 * * *` = every 2 hours).
- GitHub may pause scheduled workflows in repos with no activity for 60 days — the bot's own commits to `seen_ids.json` usually keep it active, but if alerts stop, check the Actions tab for a "re-enable" button.
