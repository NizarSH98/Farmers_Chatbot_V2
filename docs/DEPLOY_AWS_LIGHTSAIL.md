# Deploying the pilot on AWS Lightsail

Last updated: 2026-11-03

This is the expedited single-VPS route for a pilot of up to about 100 users. It
uses the same images, Compose stack, migrations, and fail-closed configuration
as [Deployment and operations](DEPLOYMENT.md), but swaps Dokploy/Traefik for a
single Caddy container (`compose.vps.yaml`). Caddy obtains and renews HTTPS
certificates automatically, and the stack needs less RAM. Everything else in
`DEPLOYMENT.md` (migrations, rollback rules, monitoring) still applies.

```text
Internet ──443──> Caddy ──> web:3000 ──/api──> api:8000 ──> PostgreSQL + Qdrant
                (edge network)                           (internal data network)
```

## 0. What it costs and why it is bounded

| Item | Choice | Price | Bounded? |
| --- | --- | --- | --- |
| Server | Lightsail Linux, 4 GB RAM, 2 vCPU, 80 GB SSD, 4 TB transfer | $24/month | Fixed bundle price. Only transfer above 4 TB is extra (not reachable at pilot scale). |
| Static IP | Lightsail static IP attached to the instance | $0 | Free while attached. Charged if left detached. |
| Snapshots | Automatic daily snapshots (7 kept) | ~$0.05/GB-month, usually $1–3 | Grows only with disk use. |
| Backups (optional) | Lightsail object-storage bucket, 5 GB plan | $1/month | Fixed bundle price. |
| Domain | Any registrar, or Route 53 | ~$10–15/year | Fixed. |
| LLM answers | OpenRouter prepaid credits | You choose | **Hard cap**: prepaid credits plus a per-key credit limit, with auto top-up off. |

AWS has no confirmed account-wide hard cap that stops Lightsail. You stay bounded
because every AWS item above is a fixed-price bundle and nothing else is
created. AWS Budgets alerts you within hours if anything unexpected appears.
The only usage-priced component is the LLM, and it is hard-capped at
OpenRouter.

Why 4 GB rather than 2 GB: PostgreSQL, Qdrant, the API (ONNX embedding model),
Next.js, and Caddy fit in about 2 GB at rest. The first knowledge bootstrap and
traffic bursts need headroom. Starting smaller saves $12/month and risks
out-of-memory restarts.

## 1. Publish the images (once per release)

The server pulls images that CI publishes to GHCR. CI publishes only from
`master`, and only when all four jobs (python, frontend, migration, security)
pass.

1. Commit the work, push the branch, open a PR to `master`, and wait for green
   CI.
2. Merge. The `images` job publishes:
   `ghcr.io/nizarsh98/farmers_chatbot_v2-{api,web,backup}:latest` and
   `:sha-<commit>`.
3. In GitHub → your profile → **Packages**, open each of the three packages →
   **Package settings** → confirm the visibility is **Public**. The repository
   is public, so the server can then pull without credentials. Check from any
   machine with `docker pull ghcr.io/nizarsh98/farmers_chatbot_v2-web:latest`.

## 2. AWS account and spending guardrails (do this before creating anything)

1. Sign up at <https://aws.amazon.com>. New accounts choose a **Free** or
   **Paid** plan. A Free-plan account cannot be charged, but it closes after
   six months unless upgraded and may not allow every service. Choose
   **Paid** for a production pilot. New paid accounts still receive the
   sign-up credits, which cover several months of this stack.
2. **Secure the root user**: account menu → *Security credentials* → assign
   MFA. Never create root access keys.
3. Create a daily-use identity: **IAM** → *Users* → *Create user* (e.g.
   `raise-admin`), console access, attach `AdministratorAccess`, enable MFA.
   Sign out of root and use this user from now on.
4. Allow that user to see billing: as root, *Account* → *IAM user and role
   access to Billing information* → **Activate**.
5. **Budget with alerts**: *Billing and Cost Management* → *Budgets* →
   *Create budget* → *Customize* → *Cost budget* → monthly, amount **$35**.
   Add alerts:
   - Actual > 50% → email
   - Actual > 80% → email
   - Forecasted > 100% → email
6. *Billing preferences* → enable **Free Tier usage alerts** and **PDF
   invoices by email**.
7. *Cost Anomaly Detection* → create a monitor for **AWS services** with an
   individual-alert email subscription and a threshold of $5.
8. If **AWS Settings → Billing → Spend limit** appears in your account, you
   can add a project spend limit as an extra layer. Do not rely on it for
   Lightsail until AWS documents that Lightsail is covered.

## 3. Create the Lightsail server

Open <https://lightsail.aws.amazon.com>.

1. **Create instance**
   - Region: **Frankfurt (eu-central-1)**. This is the closest full-allowance
     region to Lebanon. Mumbai and other Asia Pacific regions include only half
     the transfer allowance.
   - Platform **Linux/Unix** → *OS Only* → **Ubuntu 24.04 LTS**.
   - SSH key: keep the default region key. Download it from *Account → SSH
     keys* if you want to SSH from your PC. The browser **Connect using SSH**
     button works without it.
   - Network type: **Dual-stack**.
   - Plan: **$24 — 4 GB / 2 vCPU / 80 GB**.
   - Name: `raise-pilot`. Create.
2. **Static IP**: *Networking* → *Create static IP* → attach it to
   `raise-pilot`. Note the address. A detached static IP is billed, so delete
   it if you ever delete the server.
3. **Firewall**: instance → *Networking* → *IPv4 firewall*:
   - SSH TCP 22: click **Restrict to IP address** and add your own IP (and
     *Allow Lightsail browser SSH*).
   - Add **HTTPS** TCP 443.
   - Keep **HTTP** TCP 80 (Let's Encrypt and the HTTP→HTTPS redirect need it).
   - Optional: custom **UDP 443** for HTTP/3.
   - Nothing else. Never open 3000, 5432, 6333, or 8000.
   - Repeat the same rules under *IPv6 firewall*.
4. **Automatic snapshots**: instance → *Snapshots* → enable **Automatic
   snapshots** (daily, 7 kept).

## 4. Domain and DNS

The hosted guard requires HTTPS, and Google sign-in requires a real domain, so
an IP address alone will not work.

1. Use a domain or subdomain you control, e.g. `raise.example.org`.
2. At your DNS provider, create an **A record**: `raise` → the static IPv4.
   Optionally add an **AAAA record** → the instance IPv6.
3. Wait until `nslookup raise.example.org` returns the static IP before
   starting the stack. Otherwise Caddy cannot obtain the certificate.

## 5. Google sign-in (OIDC)

Pilot mode refuses to start without OIDC. Google is the quickest provider and
costs nothing. Any OIDC provider (including Amazon Cognito) works by changing
`OIDC_ISSUER_URL`.

1. <https://console.cloud.google.com> → create project `RAISE`.
2. *Google Auth Platform* → *Get started*: app name, support email, audience
   **External**, contact email.
3. *Data access*: scopes `openid`, `.../auth/userinfo.email`,
   `.../auth/userinfo.profile`. These are non-sensitive, so no Google review is
   needed.
4. *Audience*: in **Testing** status only listed test users (up to 100) can
   sign in, which works as a pilot allowlist. Add the pilot farmers' Gmail
   addresses there, or click **Publish app** to let any Google account sign in.
5. *Clients* → *Create client* → **Web application**:
   - Authorized JavaScript origin: `https://raise.example.org`
   - Authorized redirect URI: `https://raise.example.org/api/auth/callback`
6. Copy the **Client ID** and **Client secret**.

## 6. OpenRouter key with a hard spending cap

1. <https://openrouter.ai> → *Settings → Credits*: buy a fixed amount (e.g.
   $20). Leave **auto top-up off**. When credits run out, answers stop; you are
   never billed more.
2. *Keys* → *Create key* named `raise-pilot` with a **credit limit** (e.g.
   $20). Copy it.
3. Optionally lower the app's own limits in `.env` (step 7.5), e.g.
   `MAX_USER_WEEKLY_COST_USD=1.0` and `MAX_PILOT_QUERIES_PER_DAY=300`.

## 7. Server setup

Connect with the browser SSH button, or
`ssh -i LightsailDefaultKey.pem ubuntu@<static-ip>`.

```bash
# 7.1 Host preparation (Docker, log rotation, 2 GB swap, auto security updates)
git clone https://github.com/NizarSH98/Farmers_Chatbot_V2.git /tmp/raise-src
sudo bash /tmp/raise-src/deploy/vps/setup-host.sh
exit        # reconnect so the docker group applies

# 7.2 Application checkout
cd /opt/raise
git clone https://github.com/NizarSH98/Farmers_Chatbot_V2.git .

# 7.3 Generate the production .env (all internal secrets generated)
bash deploy/vps/make-env.sh raise.example.org you@example.org
```

7.4 **Save `RESTIC_PASSWORD`** from `.env` to your password manager now.

7.5 Fill the three external values:

```bash
nano .env
#   OIDC_CLIENT_ID=<Google client ID>
#   OIDC_CLIENT_SECRET=<Google client secret>
#   OPENROUTER_API_KEY=<OpenRouter key>
# Review also: ORGANIZATION_NAME, APP_DISPLAY_NAME, ADMIN_EMAILS,
#              ACCESS_POLICY, MAX_* limits.
```

```bash
# 7.6 Start: pulls images, migrates, starts api/web/caddy
bash deploy/vps/raise-vps.sh up

# 7.7 Build + activate the knowledge release (first deploy only; ~5–15 min)
bash deploy/vps/raise-vps.sh bootstrap

# 7.8 Verify
bash deploy/vps/raise-vps.sh status
```

`status` must show every service `healthy`, and `/api/healthz` must show
`"status":"ok"`, migration `20260901_0007`, a non-null `active_release_id`, and
`qdrant_reachable: true`.

7.9 **Manual acceptance** (from a phone and a laptop):

- `https://raise.example.org` loads with a valid padlock.
- Sign in with Google. The admin email from `ADMIN_EMAILS` sees admin
  controls; a second account does not.
- Ask one English and one Arabic question. Answers stream and cite sources.
- Upload and download a small project file.

If the API keeps restarting, run `bash deploy/vps/raise-vps.sh logs api`. A
configuration problem appears as one line, `Unsafe pilot web configuration:
<list of keys>`. Fix those keys in `.env` and run `up` again.

## 8. Backups

- **Day 1:** automatic Lightsail snapshots (step 3.4) capture the whole disk,
  including PostgreSQL and uploaded files.
- **Recommended within the first week:** encrypted off-server backups with
  restic.
  1. Lightsail → *Storage* → *Create bucket* (same region, **$1** plan, name
     e.g. `raise-backups-<random>`).
  2. Bucket → *Permissions* → **Create access key**. Copy the key ID and
     secret.
  3. In `.env`:

     ```text
     RESTIC_REPOSITORY=s3:https://s3.eu-central-1.amazonaws.com/<bucket-name>/raise
     BACKUP_S3_ACCESS_KEY_ID=<key id>
     BACKUP_S3_SECRET_ACCESS_KEY=<secret>
     BACKUP_S3_REGION=eu-central-1
     COMPOSE_PROFILES=backup
     ```

  4. Run `bash deploy/vps/raise-vps.sh up`, then
     `docker compose logs --tail 50 backup`. A first snapshot should appear
     within minutes. Restore testing is in `DEPLOYMENT.md` §9.

## 9. Day-2 operations

| Task | Command (from `/opt/raise`) |
| --- | --- |
| Status and health | `bash deploy/vps/raise-vps.sh status` |
| Logs | `bash deploy/vps/raise-vps.sh logs api` (or `web`, `caddy`, `migrate`) |
| Deploy latest `master` | `git pull && bash deploy/vps/raise-vps.sh update` |
| Pin an exact release | `bash deploy/vps/raise-vps.sh pin <40-char-sha> && bash deploy/vps/raise-vps.sh up` |
| Roll back | `pin` the previous SHA, then `up` (only if no incompatible migration; see `DEPLOYMENT.md` §11) |
| Rebuild knowledge | `bash deploy/vps/raise-vps.sh bootstrap` |
| Stop (keeps data) | `bash deploy/vps/raise-vps.sh stop` |

`.env` sets `COMPOSE_FILE=compose.yaml:compose.vps.yaml`, so a bare
`docker compose ...` in `/opt/raise` uses the production files. Never pass
`-f compose.override.yaml` on the server, because it disables authentication.

**Scaling up later:** take a manual snapshot → *Create new instance from
snapshot* with a bigger plan (e.g. 8 GB, $44) → move the static IP to it →
delete the old instance. DNS does not change. Beyond one server, move
PostgreSQL to a managed database and storage to S3 (`STORAGE_BACKEND=s3`).

## 10. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Browser shows certificate error | DNS not pointing at the static IP yet, or port 80 closed | Fix the A record and firewall, then `docker compose restart caddy` |
| `up` fails: `APP_DOMAIN must be set` | `.env` was not generated by `make-env.sh` | Add `APP_DOMAIN` and `ACME_EMAIL` |
| `pull` fails: `denied` | GHCR package is private | Make the three packages public (§1.3) |
| API unhealthy: `Unsafe pilot web configuration` | Missing or weak `.env` value | Fix the named keys |
| Google error `redirect_uri_mismatch` | Redirect URI differs from `.env` | Use exactly `https://<domain>/api/auth/callback` in both |
| Answers say knowledge is unavailable | Bootstrap not run or failed | `bash deploy/vps/raise-vps.sh bootstrap` |
| Answers fail with a provider error | OpenRouter credits exhausted or key limit reached | Top up deliberately or raise the key limit |
| Containers restart and `free -h` shows no free memory | Plan too small | Scale up (§9) |
