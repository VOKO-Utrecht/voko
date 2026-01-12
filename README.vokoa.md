# Voedselkollektief Amersfoort Fork

This is a fork of [VOKO Utrecht](https://github.com/VOKO-Utrecht/voko) for Voedselkollektief Amersfoort.

## What's Different?

- Added `webapp/vokoa/` settings module for Voedselkollektief Amersfoort
- All settings configured via environment variables (see `.env.production.example`)

## Production Deployment

1. Use settings: `VOKO_ENV=vokoa.settings.container`
2. Configure environment variables from `.env.production.example`
3. Run: `docker-compose up -d`

## Keeping in Sync with Upstream

```bash
# Add upstream
git remote add upstream https://github.com/VOKO-Utrecht/voko.git

# Sync
git fetch upstream
git rebase upstream/main

# If conflicts, they should only be in webapp/vokoa/ or this file
```

## Documentation

See main [README.md](README.md) for full VOKO documentation.
