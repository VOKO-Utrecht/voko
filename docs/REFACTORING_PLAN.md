# VOKO Organization-Agnostic Refactoring Plan

This document describes the plan to make the VOKO codebase organization-agnostic, allowing it to be used by different food collectives (VOKO Utrecht, VOKO Amersfoort, etc.) without code changes.

## Background

The codebase was originally built for VOKO Utrecht and contains hardcoded references to:
- Organization name, email, website
- Static content pages (regulations, privacy policy)
- External documentation links

This refactoring separates **code** from **configuration** and **content**.

## Architecture Decisions

### Configuration (Organization Settings)
**Solution**: Environment variables with Utrecht defaults for backwards compatibility.

| Setting | Environment Variable | Default (Utrecht) |
|---------|---------------------|-------------------|
| Organization name | `ORGANIZATION_NAME` | VOKO Utrecht |
| Short name | `ORGANIZATION_SHORT_NAME` | VOKO Utrecht |
| Legal name | `ORGANIZATION_LEGAL_NAME` | Stichting Financiën VOKO Utrecht |
| KVK number | `ORGANIZATION_KVK` | 61879584 |
| Email | `ORGANIZATION_EMAIL` | info@vokoutrecht.nl |
| Supplier email | `ORGANIZATION_SUPPLIER_EMAIL` | boeren@vokoutrecht.nl |
| Website | `ORGANIZATION_WEBSITE` | https://www.vokoutrecht.nl |

### Static Content (Regulations, Privacy Policy)
**Solution**: Django Flatpages - editable via Django Admin with TinyMCE rich text editor.

- Regulations page → Flatpage at `/reglement/`
- Privacy policy → Flatpage at `/privacy/`
- Each organization creates their own content via admin

### External Documentation Links
**Solution**: Remove hardcoded links from templates. Organizations can add their own links via the existing "Links" feature in Django Admin (visible on `/docs/` page).

## Implementation PRs

### PR 1: Cleanup + Externalize Organization Settings

**Scope**: Fix Copilot review comments, delete duplicate `vokoa/` module, make org config from env vars.

#### Tasks

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 1 | Replace deprecated `distutils.strtobool` | `vokou/settings/container.py` | |
| 2 | Fix `ALLOWED_HOSTS` crash (use `.get()`) | `vokou/settings/container.py` | |
| 3 | Add missing `POSTGRES_PORT` | `vokou/settings/container.py` | |
| 4 | Move import outside loop | `ordering/cron.py` | |
| 5 | Fix context processor error handling (`getattr`) | `vokou/context_processors.py` | |
| 6 | Fix template URL slice | `templates/partials/footer.html` | |
| 7 | Add `__all__` to prevent namespace pollution | `vokou/settings/base.py` | |
| 8 | Delete `webapp/vokoa/` directory | - | |
| 9 | Delete `README.vokoa.md` | - | |
| 10 | Delete `.env.production.example` | - | |
| 11 | Externalize `ORGANIZATION_*` settings | `vokou/settings/base.py` | |
| 12 | Update container settings for env vars | `vokou/settings/container.py` | |
| 13 | Create `.env.example` with all variables | `.env.example` | |
| 14 | Update README with configuration docs | `README.md` | |

### PR 2: Add Flatpages + Remove Hardcoded Content

**Scope**: Enable editable static pages, migrate content, remove hardcoded links.

#### Tasks

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 1 | Add `django.contrib.flatpages` to INSTALLED_APPS | `vokou/settings/base.py` | |
| 2 | Add `django.contrib.sites` to INSTALLED_APPS | `vokou/settings/base.py` | |
| 3 | Add `SITE_ID = 1` setting | `vokou/settings/base.py` | |
| 4 | Create custom FlatPageAdmin with TinyMCE | `vokou/admin.py` | |
| 5 | Add flatpages URL config | `vokou/urls.py` | |
| 6 | Create flatpage base template | `templates/flatpages/default.html` | |
| 7 | Create data migration for regulations | New migration | |
| 8 | Create data migration for privacy policy | New migration | |
| 9 | Update regulations view to use flatpage | `vokou/views.py`, `vokou/urls.py` | |
| 10 | Remove hardcoded regulations content | `templates/partials/regulations.html` | |
| 11 | Remove transport manual links | `templates/transport/ride.html` | |
| 12 | Remove car info link | `templates/transport/cars.html` | |
| 13 | Replace hardcoded email with template var | `templates/accounts/register_thanks.html` | |
| 14 | Replace hardcoded org name with template var | `templates/accounts/register_thanks.html` | |

## Migration Guide

### For VOKO Utrecht (Existing Deployment)

1. **No environment variable changes needed** - defaults are Utrecht values
2. After PR 2 is deployed, create Flatpages via Django Admin:
   - Go to `/admin/flatpages/flatpage/`
   - Create page with URL `/reglement/`, paste regulations content
   - Create page with URL `/privacy/`, paste privacy policy content
3. Optionally add external links via `/admin/docs/link/`:
   - Transport manual (NL): https://vokoutrecht.nl/transport/
   - Transport manual (EN): https://vokoutrecht.nl/transport-tasks/
   - Car borrowing info: https://vokoutrecht.nl/vervoer-regelen

### For New Organizations (e.g., VOKO Amersfoort)

1. Fork/clone the repository
2. Create deployment configuration (separate repo recommended):
   ```bash
   # .env.production
   ORGANIZATION_NAME=Voedselkollektief Amersfoort
   ORGANIZATION_SHORT_NAME=VOKO Amersfoort
   ORGANIZATION_LEGAL_NAME=Stichting Financiën Voedselkollektief Amersfoort
   ORGANIZATION_KVK=58876219
   ORGANIZATION_EMAIL=info@voedselkollektief.nl
   ORGANIZATION_SUPPLIER_EMAIL=boeren@voedselkollektief.nl
   ORGANIZATION_WEBSITE=https://www.voedselkollektief.nl
   # ... other settings (database, email, etc.)
   ```
3. Deploy the application
4. Create Flatpages via Django Admin with your organization's content
5. Optionally add Links for external documentation

## Testing Locally

### Test with different organization settings:

```bash
# Option 1: Environment variables
ORGANIZATION_NAME="Test VOKO" python manage.py runserver --settings=vokou.settings.development

# Option 2: Use .env file with docker-compose
cp .env.example .env.local
# Edit .env.local with test values
docker-compose --env-file .env.local up
```

## Related Issues/PRs

- Original PR: https://github.com/VOKO-Utrecht/voko/pull/405
- GitHub Copilot review comments addressed in PR 1

## Questions/Decisions for VOKO Utrecht

1. **Regulations content**: The current regulations are Utrecht-specific. After PR 2, this will be a Flatpage. Please review and update via admin after deployment.

2. **External documentation links**: Currently hardcoded links to vokoutrecht.nl will be removed. Add them as Links in admin if you want them visible on the /docs/ page.
