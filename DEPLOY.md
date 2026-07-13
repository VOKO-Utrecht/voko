# VOKO Deployment Guide

This document covers everything that needs to be done manually to get the new
Docker + Ansible setup running, and how to migrate from the current bare-metal setup.

---

## Prerequisites (one-time, manual)

### 1. Provision a Linux server

Ensure you have an Ubuntu 22.04 server running at `leden.vokoutrecht.nl` with
root SSH access. If migrating an existing server, skip provisioning but verify
the OS version.

### 2. Create a MaxMind account (for geo-blocking)

1. Register a **free** account at https://www.maxmind.com/en/geolite2/signup
2. After login, go to **My License Key** and generate a new key
3. Note your **Account ID** and **License Key** — you'll need these in step 4

### 3. Generate a GitHub Actions deploy SSH key

This key allows GitHub Actions to SSH into the server as `voko` and `voko_acc`.

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/voko_deploy_key -N ""
```

- Add the **private key** to GitHub repo secrets as `SSH_KEY`
  (Settings → Secrets and variables → Actions → New repository secret)
- You'll add the **public key** to `vault.yml` in the next step

### 4. Set up Ansible vault

```bash
cd infra/ansible

# Copy the example vault file
cp vars/vault.example.yml vars/vault.yml

# Fill in all values in vault.yml (use your editor)
# Key things to fill in:
#   - github_deploy_key_pub: contents of ~/.ssh/voko_deploy_key.pub
#   - maxmind_account_id + maxmind_license_key: from step 2
#   - prod_django_secret_key: generate with: python3 -c "import secrets; print(secrets.token_urlsafe(50))"
#   - prod_postgres_password: strong random password
#   - prod_mollie_api_key: from Mollie dashboard (live key)
#   - acc_mollie_api_key: from Mollie dashboard (test key)
#   - certbot_email: email for Let's Encrypt expiry notices

# Encrypt the vault
ansible-vault encrypt vars/vault.yml
# Choose a vault password and store it safely (e.g. in your team password manager)
```

### 5. Install Ansible locally

```bash
pip install ansible
ansible-galaxy collection install -r infra/ansible/requirements.yml
```

### 6. (Optional) Add your team's IPs for SSH restriction

In `infra/ansible/vars/main.yml`, fill in `ssh_allowed_ips`:

```yaml
ssh_allowed_ips:
  - 1.2.3.4   # Your office/home IP
  - 5.6.7.8
```

If left empty, SSH is open to all IPs (less secure but simpler).

---

## First-time server provisioning

Run the Ansible playbook. This installs Docker, nginx, certbot, sets up users,
firewall, geo-blocking, and deploys all scripts and env files.

```bash
cd infra/ansible

# Test connectivity first
ansible -i inventory.yml all -m ping --ask-vault-pass

# Run the full playbook
ansible-playbook -i inventory.yml playbook.yml --ask-vault-pass
```

This takes about 5–10 minutes on a fresh server.

**What Ansible sets up:**
- `voko` and `voko_acc` users with SSH keys
- SSH hardening (no password auth, limited users)
- ufw firewall (only 80/443/22 open)
- fail2ban (SSH brute-force protection)
- Docker CE + compose plugin
- nginx with GeoIP2 (NL + BE allowed by default)
- Let's Encrypt SSL certificates for both domains
- `/home/voko/scripts/deploy_prod.sh`
- `/home/voko_acc/scripts/deploy.sh`
- `.env` files with all secrets
- Daily DB backup cron job

---

## Database migration (cutover from old setup)

Do this during a **low-traffic window** (e.g. weekday evening). The site will
be unavailable for roughly 5–10 minutes.

### Step 1 — Dump the existing production database

SSH into the current server as the `voko` user (or root):

```bash
pg_dump -U voko voko > /tmp/voko_prod_$(date +%Y%m%d).sql
```

Copy it to your local machine:

```bash
scp voko@leden.vokoutrecht.nl:/tmp/voko_prod_*.sql ./voko_prod_backup.sql
```

### Step 2 — Start only the new DB container on the new server

```bash
ssh voko@leden.vokoutrecht.nl
cd ~/voko
docker compose -f docker-compose.deploy.yml --env-file .env up -d db
```

Wait for it to be healthy:

```bash
docker exec voko_db_prod pg_isready -U voko
```

### Step 3 — Create the database and user inside the container

The postgres container starts with `POSTGRES_USER=voko` and `POSTGRES_PASSWORD`
from the env file, but the default database is `postgres`. Create the `voko` db:

```bash
docker exec voko_db_prod psql -U voko -c "CREATE DATABASE voko;"
```

(If the `POSTGRES_NAME=voko` env var is set, this DB is created automatically
on first start — check with `docker exec voko_db_prod psql -U voko -l`)

### Step 4 — Take a final dump and restore it

Back on the **old server**, stop the app and take a final dump:

```bash
# Stop the old app (adjust for however it's currently running, e.g. systemctl)
sudo systemctl stop voko   # or: supervisorctl stop voko

# Final dump
pg_dump -U voko voko > /tmp/voko_final_$(date +%Y%m%d_%H%M%S).sql
```

Copy it to the new server and restore:

```bash
# Copy to new server
scp /tmp/voko_final_*.sql voko@leden.vokoutrecht.nl:/tmp/

# On new server: restore into the Docker DB
ssh voko@leden.vokoutrecht.nl
cat /tmp/voko_final_*.sql | docker exec -i voko_db_prod psql -U voko -d voko
```

### Step 5 — Start the full stack

```bash
cd ~/voko
docker compose -f docker-compose.deploy.yml --env-file .env up -d
```

Check logs:

```bash
docker compose -f docker-compose.deploy.yml logs -f web
```

The container runs migrations automatically on startup (they should be a no-op
since you restored a current DB).

### Step 6 — Verify and cut over

1. Add a temporary `/etc/hosts` entry on your machine pointing `leden.vokoutrecht.nl`
   to the new server IP, and verify the site works
2. Once confirmed, update DNS to point to the new server
3. Keep the old server running for 24–48h during DNS propagation
4. After DNS has propagated and the old server is no longer receiving traffic,
   decommission it

### Repeat for acceptance

Follow the same steps for the acceptance environment using `voko_acc` user,
`docker-compose.deploy.yml` (the same file — env vars in `.env` differentiate them), and the acceptance DB.

---

## Regular deploy workflow (after initial setup)

### Deploy to production

Happens automatically on every push to `main` via GitHub Actions.

To trigger manually:

```bash
ssh voko@leden.vokoutrecht.nl ~/scripts/deploy_prod.sh
```

### Deploy a branch to acceptance

Via GitHub Actions UI: Actions → Deploy → Run workflow → enter branch name.

Or manually:

```bash
ssh voko_acc@leden.vokoutrecht.nl ~/scripts/deploy.sh my-branch-name
```

---

## Ongoing operations

### View logs

```bash
# Production
docker compose -f ~/voko/docker-compose.deploy.yml logs -f web

# Acceptance
docker compose -f ~/voko/docker-compose.acc.yml logs -f web
```

### Run Django management commands

```bash
# Production
docker exec voko_web_prod uv run python manage.py <command> --settings=vokou.settings.docker_production

# Acceptance
docker exec voko_web_acc uv run python manage.py <command> --settings=vokou.settings.docker_acceptance
```

### Manual database backup

```bash
sudo /usr/local/bin/voko-backup.sh
```

Backups are stored in `/var/backups/voko/` and retained for 30 days.

### Restore a backup

```bash
# Stop the web container first to prevent writes during restore
docker stop voko_web_prod

# Restore
gunzip -c /var/backups/voko/prod_20240101_023000.sql.gz | \
    docker exec -i voko_db_prod psql -U voko -d voko

# Start web again
docker start voko_web_prod
```

### Update secrets / env vars

```bash
cd infra/ansible
ansible-vault edit vars/vault.yml

# Re-run only the app role to redeploy env files
ansible-playbook -i inventory.yml playbook.yml --tags app --ask-vault-pass

# Then restart the containers to pick up the new env
ssh voko@leden.vokoutrecht.nl \
    "docker compose -f ~/voko/docker-compose.deploy.yml --env-file ~/voko/.env up -d"
```

### Update allowed countries for geo-blocking

Edit `infra/ansible/vars/main.yml`, update the `allowed_countries` list, then:

```bash
ansible-playbook -i inventory.yml playbook.yml --tags nginx --ask-vault-pass
```

---

## Re-running Ansible (idempotent)

The playbook is fully idempotent — safe to re-run at any time to apply config
changes. To apply only specific changes, use tags:

```bash
ansible-playbook -i inventory.yml playbook.yml --tags nginx --ask-vault-pass
ansible-playbook -i inventory.yml playbook.yml --tags app --ask-vault-pass
ansible-playbook -i inventory.yml playbook.yml --tags firewall --ask-vault-pass
```
