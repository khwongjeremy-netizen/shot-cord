# Git command cheatsheet — Striker Analytics / football

Copy any block into Terminal. Run from your project folder:

```bash
cd /Users/JeremyWong/Desktop/football
```

---

## First-time setup (local only — no GitHub required)

```bash
cd /Users/JeremyWong/Desktop/football
git init
```

```bash
git config user.name "Your Name"
git config user.email "you@example.com"
```

```bash
git add .
git status
git commit -m "Initial commit: Striker Analytics app"
```

---

## Daily workflow

```bash
cd /Users/JeremyWong/Desktop/football
git status
```

```bash
git diff
```

```bash
git add track_enigine.py main.py
git commit -m "Describe what you changed"
```

```bash
git add .
git commit -m "Describe what you changed"
```

---

## Branches (try ideas without breaking main)

```bash
git branch
```

```bash
git checkout -b refactor/telemetry-engine
```

```bash
git checkout main
```

```bash
git checkout refactor/telemetry-engine
```

```bash
git branch -d refactor/telemetry-engine
```

Merge a finished branch into main:

```bash
git checkout main
git merge refactor/telemetry-engine
```

---

## See history and compare versions

```bash
git log --oneline -15
```

```bash
git log --oneline --graph --all -20
```

```bash
git show HEAD
```

```bash
git diff main..refactor/telemetry-engine
```

```bash
git diff HEAD~1
```

---

## Undo / restore (careful — read what each does)

Discard **uncommitted** edits in one file:

```bash
git restore track_enigine.py
```

Unstage a file (keep your edits on disk):

```bash
git restore --staged track_enigine.py
```

Go back to last commit for one file (loses uncommitted changes):

```bash
git checkout HEAD -- track_enigine.py
```

Undo last commit but **keep** your file changes:

```bash
git reset --soft HEAD~1
```

View an old version of a file (read-only preview):

```bash
git show HEAD~3:track_enigine.py
```

---

## Stash (park work temporarily)

```bash
git stash push -m "WIP before switching branch"
```

```bash
git stash list
```

```bash
git stash pop
```

---

## Tags (mark a known-good snapshot)

```bash
git tag -a v1.0-stable -m "Stable baseline before refactor"
```

```bash
git tag
```

```bash
git checkout v1.0-stable
```

```bash
git checkout main
```

---

## Optional: connect to GitHub later

Create an empty repo on GitHub first, then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/football.git
git branch -M main
git push -u origin main
```

Push a feature branch:

```bash
git push -u origin refactor/telemetry-engine
```

See remotes:

```bash
git remote -v
```

---

## Useful one-liners for this project

Commit only the tracking engine:

```bash
git add track_enigine.py && git commit -m "Update tracking engine"
```

Commit only the UI:

```bash
git add main.py && git commit -m "Update Tkinter UI"
```

See what changed in the last commit:

```bash
git show --stat
```

List files in the repo:

```bash
git ls-files
```

---

## Quick reference

| Goal | Command |
|------|---------|
| Where am I? | `git status` |
| What changed? | `git diff` |
| Save snapshot | `git add .` then `git commit -m "message"` |
| New experiment branch | `git checkout -b branch-name` |
| Switch branch | `git checkout branch-name` |
| History | `git log --oneline -15` |
| Compare branches | `git diff main..other-branch` |
