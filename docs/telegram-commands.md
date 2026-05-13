# Telegram / OpenClaw Commands

PMO Studio's chat adapter is:

```text
pmo_studio/interfaces/telegram_adapter.py
```

It returns Markdown text and optional `MEDIA:<path>` lines. It does not send messages by itself.

## Commands

```text
/pmo help
/pmo init <slug> --customer "Tên KH" --brief "Mô tả" [--source file]
/pmo generate [slug] all|po|pm|ba|ic --from-sources --refine --llm noop|9router
/pmo ba [slug]
/pmo trace [slug]
/pmo gates [slug] [--include-c]
/pmo status [slug]
/pmo list [--refresh]
/pmo recent
/pmo export [slug] --format html|docx|zip|all [--send] [--include-redacted-sources]
/pmo baseline [slug] v1.0 --approved
/pmo benchmark [--send] [--no-docx]
/pmo doctor [slug]
```

## Recent project fallback

If `[slug]` is omitted, adapter uses the most recently updated project from registry.

## Approval required

These commands require approval:

```text
baseline
official-quotation
signoff
```

Without approval, the adapter returns a warning and approval token.

## Example smoke

```python
from pathlib import Path
from pmo_studio.interfaces.telegram_adapter import handle_command

root = Path('/tmp/pmo-chat')
print(handle_command('/pmo help', root=root))
```
