---
name: salesianos-deploy
description: Salesianos FEST deploy workflow to server_rudy via SSH manager. Git pull, docker compose build/up for backend/frontend/proxy, verification. Trigger: deploy, subir al server, push production, deploy salesianos.
allowed-tools: Read, Bash
---

# Salesianos FEST — Deploy Workflow

> Production deploy for `server_rudy` (100.103.61.65, user `consola`).
> Project root on server: `/home/consola/Aplicaciones/Salesianos/`
> Domain: `salesianosfest.pe` (HTTPS via Cloudflare Tunnel → Nginx proxy → Django)

---

## 1. Activation Contract

Use this skill when:

- Code is committed to `master` branch and ready for production
- User says "subir al server", "deploy", "publicar cambios"
- Only **backend** and/or **frontend** changed (db, proxy rarely need rebuild)

Do NOT use when:

- Only db schema changes (run migrations separately)
- Local development

---

## 2. Pre-Deploy Checklist (run FIRST, ALWAYS)

SSH into `server_rudy` and verify before doing anything:

```bash
# Connectivity + state
ssh-manager_ssh_execute(server=server_rudy, command="docker ps --filter name=salesianos --format 'table {{.Names}}\t{{.Status}}'")
ssh-manager_ssh_execute(server=server_rudy, command="cd ~/Aplicaciones/Salesianos && git status --short")

# .env is PRODUCTION (not localhost)
ssh-manager_ssh_execute(server=server_rudy, command="cd ~/Aplicaciones/Salesianos && grep -E '^(ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS|NEXT_PUBLIC_FRONTEND_URL|DEBUG)' .env")

# GitHub reachable (DNS)
ssh-manager_ssh_execute(server=server_rudy, command="curl -s -o /dev/null -w '%{http_code}' https://github.com/MicroCats37/Salesianos.git/info/refs?service=git-upload-pack")
```

Expected:

- All 5 salesianos containers **healthy** or **Up**
- `git status` → empty (clean)
- `.env` → `ALLOWED_HOSTS=salesianosfest.pe,www.salesianosfest.pe`, `CSRF_TRUSTED_ORIGINS=https://...`, `NEXT_PUBLIC_FRONTEND_URL=https://salesianosfest.pe`, `DEBUG=False`
- HTTP **200** from GitHub

If any check fails, **STOP and report to user** before proceeding.

---

## 3. Execution Steps

### Step 1: Backup .env (always)

```bash
ssh-manager_ssh_execute(
  server=server_rudy,
  command="cd ~/Aplicaciones/Salesianos && cp .env .env.backup-$(date +%Y%m%d-%H%M)"
)
```

### Step 2: Local — commit and push (run from user's Windows machine)

```bash
cd "C:\Users\Usuario\Desktop\Aplicaciones\CST\Salesianos"
git add <files>
git commit -m "<conventional commit message>"
git push origin master
```

User must have GitHub auth configured. If push fails with auth error → tell user to push from their machine.

### Step 3: Pull on server

```bash
ssh-manager_ssh_execute(
  server=server_rudy,
  command="cd ~/Aplicaciones/Salesianos && git pull origin master"
)
```

### Step 4: Build (background, non-blocking)

Use `nohup` because `--no-cache` can take 5+ minutes and would timeout the SSH call:

```bash
ssh-manager_ssh_execute(
  server=server_rudy,
  command="cd ~/Aplicaciones/Salesianos && nohup bash -c 'docker compose build --no-cache backend frontend > /tmp/build.log 2>&1' > /dev/null 2>&1 & echo \"BUILD PID: $!\""
)
```

If only one service changed (e.g., only backend), build only that one:

```bash
docker compose build --no-cache backend
```

If only filemode/perms changed (no content) → use cached build:

```bash
docker compose build backend   # WITHOUT --no-cache
```

### Step 5: Poll build status

```bash
ssh-manager_ssh_execute(server=server_rudy, command="(pgrep -f 'docker compose build' > /dev/null && echo RUNNING || echo DONE) && tail -10 /tmp/build.log")
```

Repeat until `DONE`. Last lines should show `<service>  Built`.

### Step 6: Recreate containers (no cache for db/proxy/scraper)

```bash
ssh-manager_ssh_execute(
  server=server_rudy,
  command="cd ~/Aplicaciones/Salesianos && docker compose up -d --no-deps --force-recreate backend frontend"
)
```

Add `proxy` if nginx.conf changed. Never include `db` (data loss risk).

### Step 7: Verify

```bash
ssh-manager_ssh_execute(
  server=server_rudy,
  command="sleep 10 && docker ps --filter name=salesianos --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
)
```

Expected: `salesianos_backend` → **Up X seconds (healthy)**. Frontend may not show healthy (no healthcheck defined) but should be Up.

### Step 8: Verify Django settings loaded production values

```bash
ssh-manager_ssh_execute(
  server=server_rudy,
  command="docker compose exec backend python manage.py shell -c \"from django.conf import settings; print('TRUSTED:', settings.CSRF_TRUSTED_ORIGINS, 'PROXY:', settings.SECURE_PROXY_SSL_HEADER)\""
)
```

Expected: `TRUSTED: {'https://salesianosfest.pe', 'https://www.salesianosfest.pe'}` and `PROXY: ('HTTP_X_FORWARDED_PROTO', 'https')`.

---

## 4. Pitfalls (LESSONS LEARNED — read before any deploy)

### ❌ `entrypoint.sh` permission denied

**Symptom**: `error during container init: exec: "/app/docker/entrypoint.sh": permission denied`

**Cause**: Windows checkouts drop the `+x` bit. The fix is now in `backend/Dockerfile` (added `RUN chmod +x /app/docker/entrypoint.sh` after the COPY).

**Recovery if it happens again**: `chmod +x backend/docker/entrypoint.sh` then `docker compose build backend` (cached, fast).

### ❌ .env has localhost values in production

**Symptom**: CSRF 403 errors on `/admin/login/`, redirects to `http://localhost:7000`.

**Cause**: Whoever last wrote `.env` used `localhost` (probably from `.env.example` defaults).

**Fix**: Manually rewrite `.env` with production values. NEVER commit `.env` to git (it's gitignored).

### ❌ Local uncommitted changes block `git pull`

**Symptom**: `error: Your local changes to the following files would be overwritten by merge`.

**Fix**: Inspect with `git status` → either `git checkout -- <file>` (discard) or `git stash` (save) or commit the change first.

### ❌ GitHub 404 on first pull

**Symptom**: `git pull` fails with auth prompt even though repo is "public".

**Cause**: GitHub takes a few minutes to propagate "made public" changes to their CDN. The repo IS public but DNS/view routes return 404 until cache invalidates.

**Verify with**: `curl -s -o /dev/null -w '%{http_code}' https://github.com/MicroCats37/Salesianos.git/info/refs?service=git-upload-pack` → must return **200**.

### ❌ Build timeout via SSH

**Symptom**: `MCP error -32001: Request timed out` during `docker compose build`.

**Cause**: Build takes longer than 60-300s SSH call timeout.

**Fix**: Use `nohup ... &` to background the build, then poll `/tmp/build.log` separately.

### ❌ Proxy not recreating after nginx.conf change

**Symptom**: Browser still hits old proxy config.

**Fix**: Include `proxy` in the `docker compose up -d` command: `docker compose up -d --no-deps --force-recreate backend frontend proxy`.

---

## 5. Decision Gates

| Situation | Action |
|-----------|--------|
| Only backend changed | Build backend only, recreate only backend |
| Only frontend changed | Build frontend only, recreate only frontend |
| nginx.conf in `proxy/` changed | Include `proxy` in `up -d` |
| Django settings changed | Backend restart picks up; verify with `manage.py shell -c` |
| New Python dependency | Backend rebuild with `--no-cache` |
| New npm dependency | Frontend rebuild with `--no-cache` |
| `entrypoint.sh` content changed | Backend rebuild (no `--no-cache` needed for this small file) |
| DB schema changed | Run `docker compose exec backend python manage.py migrate` BEFORE recreate |
| User says "just push it" | Run pre-deploy checklist first — don't skip |

---

## 6. Quick Reference (one-liner deploy)

If pre-checks pass and only backend/frontend code changed:

```bash
# Local
cd "C:\Users\Usuario\Desktop\Aplicaciones\CST\Salesianos"
git add -A && git commit -m "..." && git push origin master

# Remote
ssh-manager_ssh_execute(server=server_rudy, command="cd ~/Aplicaciones/Salesianos && cp .env .env.backup-$(date +%Y%m%d-%H%M) && git pull origin master")

# Build (background — see step 4 for full command)

# Recreate
ssh-manager_ssh_execute(server=server_rudy, command="cd ~/Aplicaciones/Salesianos && docker compose up -d --no-deps --force-recreate backend frontend")

# Verify
ssh-manager_ssh_execute(server=server_rudy, command="sleep 10 && docker ps --filter name=salesianos --format 'table {{.Names}}\t{{.Status}}'")
```

---

## 7. References

- `backend/config/settings/production.py` — Django prod settings (SECURE_PROXY_SSL_HEADER added)
- `backend/Dockerfile` — has `RUN chmod +x /app/docker/entrypoint.sh` (entrypoint filemode fix)
- `.env.example` — template with production values for salesianosfest.pe
- `proxy/nginx.conf` — sends `X-Forwarded-Proto: https` (Cloudflare-aware)
- `.agent/skills/deployment-procedures/SKILL.md` — generic deployment principles
- `.agent/skills/server-management/SKILL.md` — server ops principles

Base directory: `C:\Users\Usuario\Desktop\Aplicaciones\CST\Salesianos\.agent\skills\salesianos-deploy`