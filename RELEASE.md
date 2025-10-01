# Release Process

This document describes how to create a new release of markdpy.

## Prerequisites

Before creating a release, ensure:

1. All tests pass (`pytest`)
2. Code is properly formatted (`black`, `ruff`)
3. Documentation is up to date
4. Version number follows [Semantic Versioning](https://semver.org/)

## Release Steps

### 1. Update Version Number

Update the version in `pyproject.toml`:

```toml
[project]
name = "markdpy"
version = "1.0.0"  # Update this
```

### 2. Commit Version Changes

```bash
git add pyproject.toml
git commit -m "chore: bump version to 1.0.0"
git push origin main
```

### 3. Create and Push Tag

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release v1.0.0"

# Push tag to GitHub
git push origin v1.0.0
```

### 4. Automated Release Process

Once the tag is pushed, GitHub Actions will automatically:

1. ✅ **Build** the Python package (wheel and source distribution)
2. ✅ **Generate CHANGELOG.md** from commits and PRs
3. ✅ **Create GitHub Release** with:
   - Release notes from CHANGELOG
   - Distribution files (.whl, .tar.gz)
   - Changelog file
4. ✅ **Commit CHANGELOG.md** back to the repository

## Release Types

### Stable Release

For stable releases (e.g., `v1.0.0`):

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

- Creates GitHub Release
- Not marked as pre-release

### Release Candidate (RC)

For release candidates (e.g., `v1.0.0-rc1`):

```bash
git tag -a v1.0.0-rc1 -m "Release candidate v1.0.0-rc1"
git push origin v1.0.0-rc1
```

- Creates GitHub Release marked as pre-release
- Good for testing before stable release

### Beta/Alpha Releases

For beta or alpha releases (e.g., `v1.0.0-beta.1`):

```bash
git tag -a v1.0.0-beta.1 -m "Beta release v1.0.0-beta.1"
git push origin v1.0.0-beta.1
```

- Creates GitHub Release marked as pre-release

## Commit Message Conventions

For better changelog generation, follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features (appears in 🚀 Features)
- `fix:` - Bug fixes (appears in 🐛 Bug Fixes)
- `docs:` - Documentation changes (appears in 📚 Documentation)
- `test:` - Test changes (appears in 🧪 Testing)
- `chore:` - Maintenance tasks (appears in 🔧 Maintenance)
- `perf:` - Performance improvements (appears in ⚡ Performance)
- `refactor:` - Code refactoring (appears in 🔧 Maintenance)

Examples:
```bash
git commit -m "feat: add mermaid diagram support"
git commit -m "fix: resolve badge rendering issue"
git commit -m "docs: update installation instructions"
git commit -m "perf: optimize markdown rendering"
```

## Troubleshooting

### Tag Already Exists

If you need to move a tag:

```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin :refs/tags/v1.0.0

# Create new tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Failed Release

If the release workflow fails:

1. Check GitHub Actions logs
2. Fix the issue
3. Delete the tag and release
4. Re-create the tag

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features (backward compatible)
- **PATCH** (0.0.1): Bug fixes (backward compatible)

Examples:
- `v0.1.0` → `v0.2.0`: Added new feature
- `v0.2.0` → `v0.2.1`: Fixed bug
- `v0.2.1` → `v1.0.0`: Breaking API change

## Quick Reference

```bash
# Complete release process
git add pyproject.toml
git commit -m "chore: bump version to 1.0.0"
git push origin main
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# The rest is automated! 🎉
```
