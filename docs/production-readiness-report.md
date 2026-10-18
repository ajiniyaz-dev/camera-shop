# Production readiness report

18 October 2026. Local Docker verification on `http://127.0.0.1:8080`. This report does **not** authorize public deployment.

## Current verified state

| Item | Value |
| --- | --- |
| Public site | `http://127.0.0.1:8080` (Compose + nginx, loopback only via `docker-compose.dev.yml`) |
| Health | `GET /api/health` → ok / database ok |
| Published products | 639 |
| Provenance | 555 hikvision, 84 ezviz |
| Public prices | UZS via `source_code` formulas; stored USD unchanged |
| Selection | Browser-local list with numeric soʻm total; no checkout |
| Admin | Auth, CSRF, sessions, Argon2id implemented; signed-in browser checks still open |

### Phase status

| Phase | Status |
| --- | --- |
| 1 Foundation | Complete |
| 2A/2B Schema + import schema | Complete |
| 2 Public presentation | Complete on 8080 |
| 3 Admin auth | Implemented; authorized login/logout on 8080 not observed |
| 4 Excel import | Audited; fixes rebuilt on 8080; signed-in preview not observed |
| 5 Admin catalog UI | Audited; fixes rebuilt on 8080; signed-in editor not observed |
| 6 UZS + selection | **Complete** on 8080 (see `docs/phase-6-completion-report.md`) |
| 7 Technical SEO | Implemented in source; absolute canonicals/sitemap hosts omitted while `PUBLIC_SITE_URL` is a loopback placeholder |
| 8 Production deploy | **Not started** — blocked on client inputs and ops work |

## Changes made in this pass

### Runtime

- Rebuilt and recreated only `api` and `web` (`--no-deps --build`).
- Reloaded nginx config inside the existing nginx container (upstream IP refresh).
- Left postgres, named volumes, media, env secrets, and catalog rows untouched.

### Documentation

| File | Change |
| --- | --- |
| `docs/phase-6-completion-report.md` | Docker/browser verification results |
| `docs/production-readiness-report.md` | This report |
| `docs/PROJECT_HANDOFF.md` | Phase 6 complete; next actions |
| `docs/security-strategy.md` | Public price wording: UZS display from stored USD |
| `docs/architecture.md` | Public price rendering: soʻm, not `$` |

No application code, schema, workbook, or credential changes in this pass.

## Verification results

### Automated (isolated)

| Suite | Result |
| --- | --- |
| `pytest tests/test_pricing.py tests/test_public_catalog.py` on disposable Postgres `127.0.0.1:55432` | 13 passed |
| `npm run typecheck` in `web/` | Passed |
| Frontend `*.test.mts` with `--experimental-strip-types` | 32 passed |

Disposable container removed. Compose catalog DB was not used for tests.

### Source / build

- Docker `api` and `web` images rebuilt from current source (production Next.js build inside the web image).
- Compose production shape already sets `APP_ENV=production` and `DEBUG=false` on the api service; the **local** overlay (`docker-compose.dev.yml`) forces `APP_ENV=local` so placeholder secrets work on loopback HTTP.

### Browser / API on port 8080

| Check | Result |
| --- | --- |
| Health | ok |
| Catalog total | 639 |
| Hikvision sample `12V 10A` | 38 400 сум (4 × 9600); stored 4.00 USD |
| HiLook sample | 1 104 000 сум (115 × 9600); stored 115.00 USD |
| EZVIZ sample `CS-C60P (3MP)` | 540 000 сум (50 × 10800); stored 50.00 USD |
| Soʻm price filter | Works |
| Selection add/remove/dedupe/persist | Works |
| Selection total | 1 158 000 сум for HiLook + EZVIZ monthly |
| On-request exclusion text | Shown when WD on-request is in the list |
| Checkout / cart routes | 404 |
| Security headers (nginx) | nosniff, Referrer-Policy, X-Frame-Options DENY, CSP present |
| `/robots.txt` | Allows `/ru` `/uz` `/en`; disallows `/admin`, `/api/`, private media |
| `/sitemap.xml` | Empty urlset while `PUBLIC_SITE_URL` is loopback (by design) |

### Not verified locally (needs production inputs)

- HTTPS / TLS certificate and HSTS
- `Secure` session cookies against a real HTTPS origin
- Non-loopback `PUBLIC_SITE_URL` canonicals, hreflang, Open Graph, JSON-LD site URLs, populated sitemap
- DNS (apex / www choice and redirect)
- Real phone, email, address, hours, social URLs
- Daily `pg_dump` and media-volume backup jobs on the VPS
- One restore drill on the target host
- Public internet exposure / firewall beyond loopback
- Authorized admin login and logout on 8080 (Phase 3/5)

## Already implemented (do not treat as missing)

- Modular monolith: Next.js + FastAPI + PostgreSQL + nginx Compose stack
- Argon2id passwords, server-side sessions, CSRF on admin writes, login rate limit (in-process)
- Production config guards: placeholder `SESSION_SECRET` and `DEBUG=true` rejected when `APP_ENV=production`
- Postgres on internal Compose network only in production compose; host bind is loopback:5433 in the local overlay
- Media volume; `/media/objects/` served; import paths not listed
- Public vs admin schemas; on-request labels; no checkout/payments/orders
- SEO plumbing: metadata, robots, sitemap route, JSON-LD components (absolute URLs gated on real origin)
- Health checks on api, web, nginx, postgres
- Alembic migrations applied for current schema (no pending Phase 6/7 migration)

## Security and operational blockers for release

| Blocker | Why it blocks | Owner input required |
| --- | --- | --- |
| Exact public domain | Canonicals, cookies Origin/Referer checks, TLS certs | Domain string and apex vs www choice |
| TLS certificate + HTTPS nginx | Production cookies are `Secure`; HTTP will not store them; HSTS waits on TLS | Cert path or ACME setup on Ahost |
| `PUBLIC_SITE_URL=https://…` | Until set to a non-loopback HTTPS origin, sitemap hosts and absolute SEO URLs stay omitted | Same as domain |
| Production `SESSION_SECRET` | Must be a long random non-placeholder value | Generate and set in server `.env` |
| Contact / social fields | Seeded null; do not invent | Phone, email, address, hours, social URLs if any |
| Scheduled backups | Daily `pg_dump` + media copy not automated in app code | Cron or host job + off-box retention |
| Restore drill | Spec requires one successful restore before launch | Ops time on VPS |
| Login rate limit scope | In-process only; not shared across workers/replicas | Accept single-worker or add shared limiter later (out of current architecture) |
| Phase 3/5 signed-in checks | Existing admin password unknown to automation | Operator signs in once on 8080 or staging |

## Required hosting inputs (do not invent)

1. Public hostname (and whether www or apex is canonical).
2. TLS certificate material or ACME email/method for the Ahost VPS.
3. Final `.env` values: `POSTGRES_PASSWORD`, `SESSION_SECRET`, `PUBLIC_SITE_URL`, `MEDIA_PUBLIC_BASE_URL` (HTTPS media origin), contact fields via admin after launch.
4. Confirmation that the VPS firewall publishes only 80/443 (and SSH), not Postgres.
5. Backup destination path or remote target for dumps and media copies.

## Backup / restore (existing project procedure)

Backup (example; adjust paths on the VPS):

```bash
# Custom-format DB dump (Compose service name postgres)
docker compose --env-file .env -f docker-compose.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "backup-$(date +%F).dump"

# Media volume copy (volume name may be prefixed by project)
docker run --rm -v camera-shop_catalog_media:/from -v "$(pwd)/backups:/to" alpine \
  tar czf /to/media-$(date +%F).tar.gz -C /from .
```

Restore (destructive to live data — requires explicit approval):

```bash
# Stop writers first, then:
docker compose --env-file .env -f docker-compose.yml exec -T postgres \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < backup-YYYY-MM-DD.dump
# Extract media archive back into the catalog_media volume, then recreate api/web if needed.
```

Rollback of a bad **application** release (no schema change): redeploy previous `api` and `web` images; keep postgres and volumes. If a migration must be undone, restore the pre-migration database backup — do not hand-edit production tables.

## Deployment runbook (existing Compose stack)

Do **not** run this against a public host until domain, TLS, secrets, and backups are ready. Local loopback form used today:

```bash
# From repo root, with a filled .env (never commit it)
docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# After recreating api/web only (preserves postgres + volumes):
docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml \
  up -d --no-deps --build api web
docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml \
  exec nginx nginx -s reload

# Health
curl -s http://127.0.0.1:8080/api/health
```

Production-shaped file is `docker-compose.yml` alone (postgres unpublished; nginx `:80`; api `APP_ENV=production`). TLS/HSTS server blocks are intentionally absent until the client domain is supplied — add them in `deploy/nginx.conf` (or a sibling TLS conf) at that time, then bind 443.

Migrations before traffic (only when a new revision exists and is approved):

```bash
docker compose --env-file .env -f docker-compose.yml run --rm api \
  alembic upgrade head
```

## Checklist

### Safe / already done on this machine

- [x] 639 published products preserved
- [x] UZS display live on 8080 for Hikvision, HiLook, and EZVIZ samples
- [x] Stored USD unchanged
- [x] Selection total + on-request exclusion disclosure
- [x] No checkout/payment paths
- [x] Health checks green after api/web rebuild
- [x] Isolated pricing/public/frontend tests passed
- [x] Phase 6 report updated with Docker evidence
- [x] Docs aligned on public UZS (security + architecture)

### Requires explicit approval or client input

- [ ] Commit / push of documentation or any remaining source
- [ ] Provide real domain and set `PUBLIC_SITE_URL` / `MEDIA_PUBLIC_BASE_URL`
- [ ] Install TLS and open the site beyond loopback
- [ ] Generate production `SESSION_SECRET` and DB password on the VPS
- [ ] Fill contact and social fields (do not invent)
- [ ] Schedule and test backup + restore on the VPS
- [ ] Run Alembic on production if a future migration is approved
- [ ] Sign in as the existing administrator to close Phase 3/5 browser gaps
- [ ] DNS cutover / public announce

## Verdict

The **local** informational catalog on port 8080 is feature-complete through Phase 6 (UZS + selection) with a healthy Compose stack and 639 products. It is **not** ready for public production deployment until domain, TLS, production secrets, `PUBLIC_SITE_URL`, contact details, and backup/restore ops are supplied and verified on the target host.

**Next action:** obtain the real HTTPS origin and contact details from the client; keep the site on loopback until those values and a TLS plan exist. Do not deploy publicly from this report alone.
