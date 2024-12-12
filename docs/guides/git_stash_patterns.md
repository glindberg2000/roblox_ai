# Git Stash Patterns Guide

## Basic Stash Operations

### Stash Specific Files
```bash
# Stash single file
git stash push path/to/file.py

# Stash multiple files
git stash push file1.py file2.py config.py

# Stash with message
git stash push -m "Saving API configuration changes" api/app/config.py
```

### View Stashes
```bash
# List all stashes
git stash list

# Show contents of latest stash
git stash show -p

# Show specific stash
git stash show -p stash@{0}
```

### Apply/Restore Stashes
```bash
# Apply latest stash (keeps stash in list)
git stash apply

# Apply specific stash
git stash apply stash@{1}

# Pop latest stash (removes from list)
git stash pop

# Pop specific stash
git stash pop stash@{2}
```

## Common Patterns

### Feature Work Protection
```bash
# Before switching branches
git stash push -m "feature/anthropic-integration" api/app/*.py

# After returning
git stash list  # Find your stash
git stash pop stash@{0}
```

### Multiple Related Files
```bash
# Save related changes together
git stash push -m "API config updates" \
    api/app/config.py \
    api/app/letta_router.py

# Create backup before experimenting
cp api/app/config.py api/app/config.py.backup
git stash push api/app/config.py
```

### Stash Management
```bash
# Clear all stashes
git stash clear

# Drop specific stash
git stash drop stash@{1}

# Create branch from stash
git stash branch new-feature stash@{0}
```

## VSCode/Cursor Snippets for Git Commands

Add to your shell/command snippets:

```json
{
    "Git Stash File": {
        "prefix": "gstashf",
        "body": "git stash push ${1:path/to/file}",
        "description": "Stash specific file"
    },
    "Git Stash Multiple": {
        "prefix": "gstashm",
        "body": "git stash push ${1:file1} ${2:file2}",
        "description": "Stash multiple files"
    },
    "Git Stash Show": {
        "prefix": "gstashs",
        "body": "git stash show -p stash@{${1:0}}",
        "description": "Show stash contents"
    },
    "Git Stash Pop": {
        "prefix": "gstashp",
        "body": "git stash pop stash@{${1:0}}",
        "description": "Pop specific stash"
    }
}
```

## Best Practices

1. **Always Add Messages**
   ```bash
   git stash push -m "Description of changes" file1 file2
   ```

2. **Backup Critical Files**
   ```bash
   cp important.py important.py.backup
   git stash push important.py
   ```

3. **Check Before Popping**
   ```bash
   git stash show -p stash@{0}  # Verify contents
   git stash pop stash@{0}      # Then pop
   ```

4. **Clean Up Old Stashes**
   ```bash
   git stash list
   git stash drop stash@{old_number}
   ```

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Lost stash | `git fsck --unreachable` to find dangling stashes |
| Conflict on pop | `git stash show -p > changes.patch` then `git apply changes.patch` |
| Partial stash | `git stash push -p` for interactive selection |
| Wrong stash applied | `git reset --hard` then try different stash |
``` 