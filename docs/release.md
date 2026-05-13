# Release Checklist

Current release candidate:

```text
1.0.0rc2
```

## Verify

```bash
cd /home/snail/.openclaw/workspace/pmo-studio
scripts/verify_all.sh /tmp/pmo-release-verify
scripts/install_check.sh /tmp/pmo-install-check
```

Expected final lines:

```text
VERIFY_ALL_PASS
INSTALL_CHECK_PASS
```

## Manual checks

- [ ] README quick start is accurate.
- [ ] `pmo --help` works after editable install.
- [ ] `python -m pmo_studio.cli eval --benchmark --no-docx` passes.
- [ ] ZIP bundle excludes `source/uploads`.
- [ ] ZIP bundle includes `source/redacted` only when explicitly requested.
- [ ] `/pmo baseline ...` requires approval in adapter.
- [ ] 9Router is not required for default smoke.

## CI workflows

Templates:

```text
.github/workflows/verify.yml
.github/workflows/release.yml
```

`verify.yml` runs compile/smoke/benchmark/negative checks on Python 3.11, 3.12, 3.13.

`release.yml` runs full verify and `python -m build` when pushing tags matching `v*`.

## Tag suggestion

```bash
git tag v1.0.0rc2
```

Only tag after review and commit.
