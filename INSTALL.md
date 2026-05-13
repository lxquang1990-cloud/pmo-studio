# Install PMO Studio

PMO Studio is a Python CLI package. It is designed to run offline by default; LLM usage is optional.

## Requirements

- Python 3.11 or newer
- Git
- `pip`

## Fresh clone install

```bash
git clone https://github.com/lxquang1990-cloud/pmo-studio.git
cd pmo-studio

python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

pmo --help
pytest -q
```

## Run a sample project

```bash
python -m pmo_studio.cli --root /tmp/pmo-demo scaffold

cat > /tmp/pmo-source.md <<'EOF'
Khách hàng cần eOffice quản lý văn bản, duyệt đa cấp, phân quyền phòng ban,
dashboard SLA, báo cáo quá hạn. token=secret
EOF

python -m pmo_studio.cli --root /tmp/pmo-demo init demo-project \
  --customer "Demo Customer" \
  --source /tmp/pmo-source.md

python -m pmo_studio.cli --root /tmp/pmo-demo generate demo-project all \
  --from-sources \
  --llm noop \
  --refine \
  --max-refine 2

python -m pmo_studio.cli --root /tmp/pmo-demo trace demo-project --validate
python -m pmo_studio.cli --root /tmp/pmo-demo run-gates demo-project
python -m pmo_studio.cli --root /tmp/pmo-demo export demo-project --format zip
```

Generated project files will be under:

```text
/tmp/pmo-demo/demo-project/
```

## Full verification

```bash
./scripts/verify_all.sh /tmp/pmo-release-verify
```

Expected final line:

```text
VERIFY_ALL_PASS
```

## Optional LLM mode

Default generation uses `--llm noop`, so no API key is required.

If you have a 9Router-compatible endpoint configured in your environment, you can use:

```bash
python -m pmo_studio.cli eval --benchmark --llm 9router --model Tier2
```

Without 9Router, keep using `--llm noop`.

## Common troubleshooting

### `pmo: command not found`

Activate the virtual environment and reinstall editable mode:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Or run via module:

```bash
python -m pmo_studio.cli --help
```

### Missing Python version

Use Python 3.11+:

```bash
python --version
```

### DOCX export dependency

`python-docx` is installed automatically from `pyproject.toml`. If DOCX export fails, reinstall dependencies:

```bash
python -m pip install -e ".[dev]"
```
