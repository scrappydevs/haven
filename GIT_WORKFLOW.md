# Git Push/Pull Workflow for Haven

## Quick Commands

### Pull latest changes from main
```bash
cd /Users/davidjr/Downloads/CMU/Sophomore\ 2025-2026/Hackathons/haven
git pull origin main
```

### Check what changed
```bash
git status
```

### Stage all changes
```bash
git add -A
```

### Commit your changes
```bash
git commit -m "Your commit message here"
```

### Push to main
```bash
git push origin main
```

---

## Common Scenarios

### Scenario 1: Start working (pull first)
```bash
cd /Users/davidjr/Downloads/CMU/Sophomore\ 2025-2026/Hackathons/haven
git pull origin main
```
This gets the latest code before you start working.

### Scenario 2: Save your work (commit and push)
```bash
# See what changed
git status

# Add all changes
git add -A

# Commit with a message
git commit -m "Added feature X"

# Push to GitHub
git push origin main
```

### Scenario 3: Someone else pushed (pull error)
If you get an error like "Updates were rejected", someone else pushed changes:

```bash
# Pull their changes first
git pull origin main

# If there are conflicts, you'll see conflict markers
# Edit the files to resolve conflicts, then:
git add -A
git commit -m "Merge remote changes"

# Now push
git push origin main
```

### Scenario 4: Force push (use carefully!)
**⚠️ Only use if you're sure you want to overwrite remote changes:**
```bash
git push --force-with-lease origin main
```

---

## Quick Reference

| Command | What it does |
|---------|--------------|
| `git status` | See what files changed |
| `git add -A` | Stage all changes |
| `git commit -m "message"` | Save changes locally |
| `git push origin main` | Upload to GitHub |
| `git pull origin main` | Download from GitHub |
| `git log --oneline` | See recent commits |
| `git diff` | See what changed in files |

---

## Before You Start Working
```bash
cd /Users/davidjr/Downloads/CMU/Sophomore\ 2025-2026/Hackathons/haven
git pull origin main
```

## After You Finish Working
```bash
git add -A
git commit -m "Describe what you did"
git push origin main
```

---

## Aliases (Optional - makes commands shorter)

Add these to your `~/.zshrc` or `~/.bashrc`:

```bash
alias gpull="git pull origin main"
alias gpush="git push origin main"
alias gs="git status"
alias ga="git add -A"
alias gc="git commit -m"
alias glog="git log --oneline --graph --all"
```

Then you can just type:
- `gpull` instead of `git pull origin main`
- `gpush` instead of `git push origin main`
- `gs` instead of `git status`

---

## Troubleshooting

### "Your branch is behind"
```bash
git pull origin main
```

### "Your branch is ahead"
```bash
git push origin main
```

### "Merge conflicts"
1. Open the conflicted files (marked with `<<<<<<<`)
2. Edit to keep what you want
3. Remove conflict markers
4. Save the files
5. Run:
```bash
git add -A
git commit -m "Resolve merge conflicts"
git push origin main
```

### "Uncommitted changes"
Either commit them:
```bash
git add -A
git commit -m "Save my work"
```

Or stash them temporarily:
```bash
git stash
git pull origin main
git stash pop  # brings your changes back
```
