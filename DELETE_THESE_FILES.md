# Files to Remove from opalib

The following files should be deleted as they are no longer needed with the Ollama integration:

1. `src/opalib/tokenizer.py` - Tokenization handled by Ollama
2. `src/opalib/inference.py` - Inference handled by Ollama
3. `src/opalib/hardware.py` - Hardware management handled by Ollama
4. `src/opalib/framework.py` - Framework simplified to just use Ollama

## To Delete These Files:

### Option 1: Via GitHub Web UI
1. Go to each file on GitHub
2. Click the trash icon
3. Commit the deletion

### Option 2: Via Git CLI
```bash
git rm src/opalib/tokenizer.py
git rm src/opalib/inference.py
git rm src/opalib/hardware.py
git rm src/opalib/framework.py
git commit -m "Remove redundant modules in favor of Ollama integration"
git push
```

### Option 3: Via GitHub CLI
```bash
gh api repos/DeveloperDankyMan/opalib/contents/src/opalib/tokenizer.py -X DELETE -f message="Remove redundant modules" -f sha=<commit-sha>
```

## What Remains:

After deletion, your `src/opalib/` will have:
```
src/opalib/
├── __init__.py
├── ai.py                      (Main API)
├── ollama_integration.py       (Ollama support)
├── enum_extender.py           (existing)
├── format.py                  (existing)
├── http.py                    (existing)
├── ieee754.py                 (existing)
├── libdeflate.py              (existing)
├── physics.py                 (existing)
├── promise.py                 (existing)
├── units.py                   (existing)
├── util.py                    (existing)
├── web.py                     (existing)
└── examples/                  (directory)
```

This keeps your library clean and focused on Ollama integration.
