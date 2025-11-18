# Release Process and Versioning

Documentation for OsMEN release process, versioning strategy, and publication workflow.

## Versioning Strategy

### Semantic Versioning

OsMEN follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH (e.g., 2.1.3)
```

- **MAJOR (X.0.0):** Breaking changes, incompatible API changes
- **MINOR (2.X.0):** New features, backward compatible
- **PATCH (2.0.X):** Bug fixes, backward compatible

### Version Numbering Examples

| Change Type | Example | Version Change |
|------------|---------|----------------|
| Bug fix | Fix authentication error | 2.0.0 → 2.0.1 |
| New feature | Add new agent | 2.0.0 → 2.1.0 |
| Breaking change | Change API format | 2.0.0 → 3.0.0 |
| Security patch | Fix CVE | 2.0.0 → 2.0.1 |

### Pre-Release Versions

```
2.1.0-alpha.1    # Alpha release
2.1.0-beta.2     # Beta release
2.1.0-rc.1       # Release candidate
2.1.0            # Stable release
```

## Release Branches

### Branch Strategy (Gitflow)

```
main (production)
├── develop (integration)
├── release/v2.1.0 (release prep)
├── feature/new-agent (features)
└── hotfix/security-patch (urgent fixes)
```

### Branch Policies

**main:**
- Production-ready code only
- Protected branch (requires PR + reviews)
- Tagged with version numbers
- Deployable at any time

**develop:**
- Integration branch for features
- All features merge here first
- Should always be stable

**feature/**
- Individual feature development
- Branch from `develop`
- Merge back to `develop`
- Naming: `feature/short-description`

**release/**
- Release preparation
- Branch from `develop`
- Only bug fixes, no new features
- Merge to `main` and `develop`

**hotfix/**
- Urgent fixes for production
- Branch from `main`
- Merge to `main` and `develop`

## Release Cycle

### Regular Release Schedule

- **Patch Releases:** As needed (1-2 weeks)
- **Minor Releases:** Monthly
- **Major Releases:** Quarterly or as needed

### Release Timeline

#### Week 1-3: Development
- Feature development
- Bug fixes
- Code reviews
- Merge to `develop`

#### Week 4: Release Preparation
1. **Day 1-2:** Create release branch
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/v2.1.0
   ```

2. **Day 3-4:** Testing
   - Run full test suite
   - Manual testing
   - Performance testing
   - Security scanning

3. **Day 5-6:** Bug fixes
   - Fix any issues found in testing
   - Update documentation
   - Update CHANGELOG.md

4. **Day 7:** Release
   - Merge to main
   - Tag release
   - Publish

## Release Checklist

### Pre-Release Checklist

#### Code Quality
- [ ] All tests passing (`python3 test_agents.py`)
- [ ] Linting passes (`make lint`)
- [ ] Security scan passes (`make security-check`)
- [ ] Code review completed for all changes
- [ ] No known critical bugs

#### Documentation
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if needed)
- [ ] API documentation updated
- [ ] Migration guide written (for breaking changes)
- [ ] Release notes drafted

#### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Performance tests acceptable
- [ ] Compatibility testing done
- [ ] Tested on all supported platforms

#### Security
- [ ] Security vulnerabilities addressed
- [ ] Dependencies updated
- [ ] No hardcoded secrets
- [ ] Security review completed

#### Infrastructure
- [ ] Docker images build successfully
- [ ] docker-compose configuration valid
- [ ] Database migrations tested
- [ ] Backup/restore tested

### Release Process

#### 1. Prepare Release Branch

```bash
# Create release branch
git checkout develop
git pull origin develop
git checkout -b release/v2.1.0

# Update version number
echo "2.1.0" > VERSION

# Update CHANGELOG.md
```

#### 2. Update CHANGELOG.md

```markdown
# Changelog

## [2.1.0] - 2024-11-18

### Added
- New knowledge management agent
- Support for Claude 3.5 Sonnet
- API v2 endpoints

### Changed
- Improved agent response times
- Updated UI for better accessibility

### Fixed
- Memory leak in vector search
- Authentication token expiry issues

### Security
- Updated dependencies with security patches
- Fixed XSS vulnerability in web dashboard

### Breaking Changes
- None

### Migration Guide
- No migration required for 2.0.x users
```

#### 3. Build and Test

```bash
# Build Docker images
docker-compose build

# Run full test suite
python3 test_agents.py

# Run security checks
python3 scripts/automation/validate_security.py

# Performance testing
python3 tests/performance_test.py
```

#### 4. Create Release Candidate

```bash
# Tag release candidate
git tag -a v2.1.0-rc.1 -m "Release candidate 1 for version 2.1.0"
git push origin v2.1.0-rc.1

# Build and publish RC images
docker build -t osmen/gateway:2.1.0-rc.1 .
docker push osmen/gateway:2.1.0-rc.1
```

#### 5. Testing Period

- Deploy RC to staging environment
- Run automated tests
- Manual testing
- Community testing (if applicable)
- Gather feedback

#### 6. Final Release

```bash
# Merge to main
git checkout main
git merge --no-ff release/v2.1.0 -m "Release version 2.1.0"

# Tag release
git tag -a v2.1.0 -m "Version 2.1.0"

# Push to repository
git push origin main
git push origin v2.1.0

# Merge back to develop
git checkout develop
git merge --no-ff release/v2.1.0 -m "Merge release 2.1.0 to develop"
git push origin develop

# Delete release branch
git branch -d release/v2.1.0
git push origin --delete release/v2.1.0
```

#### 7. Publish Release

```bash
# Build production images
docker build -t osmen/gateway:2.1.0 -t osmen/gateway:latest .

# Push to Docker Hub
docker push osmen/gateway:2.1.0
docker push osmen/gateway:latest

# Create GitHub Release
gh release create v2.1.0 \
  --title "OsMEN v2.1.0" \
  --notes-file RELEASE_NOTES.md \
  --verify-tag
```

#### 8. Announce Release

- [ ] Update GitHub Release page
- [ ] Post in GitHub Discussions
- [ ] Update website (if applicable)
- [ ] Social media announcement
- [ ] Email notification to users (if list exists)

## Hotfix Process

For urgent production fixes:

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/v2.0.1

# 2. Fix the issue
# ... make changes ...

# 3. Update version and changelog
echo "2.0.1" > VERSION

# 4. Test the fix
python3 test_agents.py

# 5. Merge to main
git checkout main
git merge --no-ff hotfix/v2.0.1 -m "Hotfix version 2.0.1"
git tag -a v2.0.1 -m "Version 2.0.1 - Security patch"
git push origin main v2.0.1

# 6. Merge to develop
git checkout develop
git merge --no-ff hotfix/v2.0.1
git push origin develop

# 7. Delete hotfix branch
git branch -d hotfix/v2.0.1
```

## Changelog Generation

### Manual Changelog

Use this template:

```markdown
## [VERSION] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security patches
```

### Automated Changelog

```bash
# Using git-changelog (if installed)
git-changelog -o CHANGELOG.md

# Or using GitHub CLI
gh api repos/dwilli15/OsMEN/releases/generate-notes \
  -f tag_name=v2.1.0 \
  -f previous_tag_name=v2.0.0
```

## Publishing to Registries

### Docker Hub

```bash
# Login
docker login

# Build multi-platform
docker buildx build --platform linux/amd64,linux/arm64 \
  -t osmen/gateway:2.1.0 \
  --push .

# Tag as latest
docker tag osmen/gateway:2.1.0 osmen/gateway:latest
docker push osmen/gateway:latest
```

### GitHub Container Registry

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and push
docker build -t ghcr.io/dwilli15/osmen/gateway:2.1.0 .
docker push ghcr.io/dwilli15/osmen/gateway:2.1.0
```

### PyPI (Python Package)

```bash
# Update setup.py with new version
# Build distribution
python3 -m build

# Upload to PyPI
python3 -m twine upload dist/*
```

## Automation

### GitHub Actions Workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: docker-compose build
      
      - name: Run tests
        run: python3 test_agents.py
      
      - name: Push to Docker Hub
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push osmen/gateway:${{ github.ref_name }}
      
      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

## Version Support Matrix

| Version | Release Date | End of Support | Status |
|---------|-------------|----------------|--------|
| 2.1.x | 2024-12-01 | 2025-12-01 | Planned |
| 2.0.x | 2024-11-01 | 2025-11-01 | Current |
| 1.x.x | 2023-06-01 | 2024-06-01 | EOL |

## Communication

### Release Announcement Template

```markdown
# OsMEN v2.1.0 Released! 🎉

We're excited to announce the release of OsMEN v2.1.0!

## What's New

- **New Knowledge Management Agent:** Enhanced document search and summarization
- **Claude 3.5 Support:** Now supports Anthropic's latest model
- **Performance Improvements:** 40% faster agent response times
- **Better Accessibility:** WCAG 2.1 AA compliance improvements

## Upgrade Instructions

[Link to upgrade guide]

## Breaking Changes

None! This is a backward-compatible release.

## Full Changelog

[Link to CHANGELOG.md]

## Download

- Docker: `docker pull osmen/gateway:2.1.0`
- Source: https://github.com/dwilli15/OsMEN/releases/tag/v2.1.0

Questions? Join our [Discussions](https://github.com/dwilli15/OsMEN/discussions)
```

## Post-Release Tasks

- [ ] Monitor error rates and performance
- [ ] Respond to user feedback
- [ ] Update documentation site
- [ ] Close milestone in GitHub
- [ ] Plan next release
- [ ] Archive old releases

## Resources

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Gitflow Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)

---

**Last Updated:** 2024-11-18  
**Current Version:** 2.0.0  
**Next Release:** 2.1.0 (December 2024)
