# HappyCodex npm Release Operations

## Table of Contents

- [1. Purpose](#1-purpose)
  - [1.1 What This File Is For](#11-what-this-file-is-for)
  - [1.2 Current Production State](#12-current-production-state)
- [2. Final Release Architecture](#2-final-release-architecture)
  - [2.1 npm Package Identity](#21-npm-package-identity)
  - [2.2 CLI Command Identity](#22-cli-command-identity)
  - [2.3 Native Binary Identity](#23-native-binary-identity)
  - [2.4 Platform Package Model](#24-platform-package-model)
  - [2.5 Dist Tags](#25-dist-tags)
- [3. GitHub Actions Workflows](#3-github-actions-workflows)
  - [3.1 Full Release Workflow](#31-full-release-workflow)
  - [3.2 Publish-Only Workflow](#32-publish-only-workflow)
  - [3.3 Required Secret](#33-required-secret)
  - [3.4 Provenance](#34-provenance)
- [4. Release Procedure](#4-release-procedure)
  - [4.1 Normal Full Release](#41-normal-full-release)
  - [4.2 Reusing Existing Native Artifacts](#42-reusing-existing-native-artifacts)
  - [4.3 Verification Commands](#43-verification-commands)
  - [4.4 Install Smoke Test](#44-install-smoke-test)
- [5. Versioning Policy](#5-versioning-policy)
  - [5.1 Stable Upstream-Aligned Versions](#51-stable-upstream-aligned-versions)
  - [5.2 Downstream-Only Fix Versions](#52-downstream-only-fix-versions)
  - [5.3 Platform Variant Versions](#53-platform-variant-versions)
- [6. Problems We Hit](#6-problems-we-hit)
  - [6.1 Upstream Actions Were Noisy in the Fork](#61-upstream-actions-were-noisy-in-the-fork)
  - [6.2 Native Release Builds Were Too Heavy](#62-native-release-builds-were-too-heavy)
  - [6.3 Linux musl Builds Needed Upstream-Specific Setup](#63-linux-musl-builds-needed-upstream-specific-setup)
  - [6.4 npm Rejected the Unscoped Name](#64-npm-rejected-the-unscoped-name)
  - [6.5 Publishing Must Be Platform-First](#65-publishing-must-be-platform-first)
- [7. Key Ingredients That Made It Work](#7-key-ingredients-that-made-it-work)
  - [7.1 Keep Upstream Internals Where Possible](#71-keep-upstream-internals-where-possible)
  - [7.2 Scope Only the Published Package Name](#72-scope-only-the-published-package-name)
  - [7.3 Validate Tarballs Before Publishing](#73-validate-tarballs-before-publishing)
  - [7.4 Use GitHub Actions for Native Releases](#74-use-github-actions-for-native-releases)
  - [7.5 Keep Dry Runs Mandatory Before Real Publish](#75-keep-dry-runs-mandatory-before-real-publish)
- [8. Important Files](#8-important-files)
  - [8.1 Package Metadata](#81-package-metadata)
  - [8.2 npm Staging Code](#82-npm-staging-code)
  - [8.3 npm Launcher](#83-npm-launcher)
  - [8.4 Release Workflows](#84-release-workflows)
  - [8.5 Documentation](#85-documentation)
- [9. Production Release Record](#9-production-release-record)
  - [9.1 Failed Unscoped Publish](#91-failed-unscoped-publish)
  - [9.2 Successful Scoped Publish](#92-successful-scoped-publish)
- [10. Troubleshooting](#10-troubleshooting)
  - [10.1 npm 403 Similar Package Name](#101-npm-403-similar-package-name)
  - [10.2 npm 404 Before First Publish](#102-npm-404-before-first-publish)
  - [10.3 Cargo Build Timeout or Runner Shutdown](#103-cargo-build-timeout-or-runner-shutdown)
  - [10.4 Missing Optional Dependency After Install](#104-missing-optional-dependency-after-install)
  - [10.5 Partial Publish Risk](#105-partial-publish-risk)
- [11. Future Maintenance Rules](#11-future-maintenance-rules)
  - [11.1 Before Merging Upstream](#111-before-merging-upstream)
  - [11.2 Before Releasing](#112-before-releasing)
  - [11.3 When Changing Package Names](#113-when-changing-package-names)

## 1. Purpose

### 1.1 What This File Is For

This file documents the production npm release setup for HappyCodex.

It exists because getting the fork from local changes to a working npm package required several non-obvious fixes:

- converting the npm identity from OpenAI Codex to HappyCodex,
- preserving the global command name as `happycodex`,
- building native artifacts for six platforms,
- publishing platform variants and root package in the correct order,
- adapting upstream release assumptions to a public fork using standard GitHub-hosted runners,
- handling npm's package-name similarity restriction by moving to the `@happyskillsai` scope.

The goal is to make future releases boring and debuggable.

### 1.2 Current Production State

The working npm package is:

```text
@happyskillsai/happycodex
```

The global command installed by npm is:

```text
happycodex
```

The first successful production npm version is:

```text
0.133.0
```

The verified install command is:

```bash
npm install -g @happyskillsai/happycodex
```

The verified npm metadata after publish was:

```text
latest -> 0.133.0
linux-x64 -> 0.133.0-linux-x64
linux-arm64 -> 0.133.0-linux-arm64
darwin-x64 -> 0.133.0-darwin-x64
darwin-arm64 -> 0.133.0-darwin-arm64
win32-x64 -> 0.133.0-win32-x64
win32-arm64 -> 0.133.0-win32-arm64
```

## 2. Final Release Architecture

### 2.1 npm Package Identity

HappyCodex is published under the scoped npm package:

```text
@happyskillsai/happycodex
```

This scope is required because npm rejected the unscoped package name `happycodex` as too similar to an existing package named `happy-codex`.

The package name is configured in:

```text
codex-cli/package.json
codex-cli/scripts/build_npm_package.py
```

### 2.2 CLI Command Identity

The installed global command remains:

```text
happycodex
```

This is controlled by the npm `bin` map:

```json
{
  "bin": {
    "happycodex": "bin/codex.js"
  }
}
```

The package can be scoped while the installed command remains unscoped. This is the correct npm pattern.

### 2.3 Native Binary Identity

The internal native binary is still named:

```text
codex
```

or on Windows:

```text
codex.exe
```

This is intentional. Renaming the Rust binary would create a much larger fork delta across Cargo targets, archive layouts, update checks, native install scripts, and upstream merge points.

HappyCodex currently changes the npm-facing package and command, not the internal Rust binary name.

### 2.4 Platform Package Model

The root package is a small JavaScript launcher. It depends on optional platform packages that contain the native binaries.

The root package is:

```text
@happyskillsai/happycodex@0.133.0
```

Its optional dependencies use local alias names:

```json
{
  "happycodex-linux-x64": "npm:@happyskillsai/happycodex@0.133.0-linux-x64",
  "happycodex-linux-arm64": "npm:@happyskillsai/happycodex@0.133.0-linux-arm64",
  "happycodex-darwin-x64": "npm:@happyskillsai/happycodex@0.133.0-darwin-x64",
  "happycodex-darwin-arm64": "npm:@happyskillsai/happycodex@0.133.0-darwin-arm64",
  "happycodex-win32-x64": "npm:@happyskillsai/happycodex@0.133.0-win32-x64",
  "happycodex-win32-arm64": "npm:@happyskillsai/happycodex@0.133.0-win32-arm64"
}
```

The aliases are unscoped because they are dependency aliases inside the root package. The actual package fetched from npm is scoped.

### 2.5 Dist Tags

The root package uses the normal release tag:

```text
latest
```

Platform variants use platform tags:

```text
linux-x64
linux-arm64
darwin-x64
darwin-arm64
win32-x64
win32-arm64
```

This lets the same npm package name carry both the root package version and the platform-specific variant versions.

## 3. GitHub Actions Workflows

### 3.1 Full Release Workflow

The full release workflow is:

```text
.github/workflows/happycodex-release.yml
```

Use it for normal releases when native artifacts need to be built.

It does this sequence:

1. Validate SemVer, npm dist-tag, and `NPM_TOKEN`.
2. Set the release version in source files.
3. Build native artifacts for all supported platforms.
4. Upload native package archives.
5. Stage npm tarballs from the artifacts produced by the same workflow run.
6. Verify package metadata before publishing.
7. Publish platform variants first.
8. Publish the root package last.

Supported native targets:

```text
x86_64-unknown-linux-musl
aarch64-unknown-linux-musl
x86_64-apple-darwin
aarch64-apple-darwin
x86_64-pc-windows-msvc
aarch64-pc-windows-msvc
```

### 3.2 Publish-Only Workflow

The publish-only workflow is:

```text
.github/workflows/happycodex-npm-publish.yml
```

Use it when native artifacts already exist and only npm staging or publishing needs to be retried.

This was essential after the unscoped npm publish failed. We did not need to rebuild the six native binaries. We reused artifacts from:

```text
https://github.com/happyskillsai/happycodex/actions/runs/26362610179
```

and then published from the corrected scoped package commit.

### 3.3 Required Secret

GitHub Actions needs this repository secret:

```text
NPM_TOKEN
```

The token must belong to an npm account with publish rights to:

```text
@happyskillsai/happycodex
```

For scoped packages, the npm account must be a member of the npm organization and have package publishing permissions.

### 3.4 Provenance

Both release workflows support:

```text
provenance=true
```

The workflows grant:

```yaml
id-token: write
```

This is required for `npm publish --provenance` from GitHub Actions.

The successful production publish emitted provenance transparency log entries for the platform packages and root package.

## 4. Release Procedure

### 4.1 Normal Full Release

Use the full workflow:

```bash
gh workflow run happycodex-release.yml \
  --repo happyskillsai/happycodex \
  --ref main \
  -f version=0.133.0 \
  -f npm_tag=latest \
  -f dry_run=true \
  -f provenance=true
```

If the dry run succeeds, run the real publish:

```bash
gh workflow run happycodex-release.yml \
  --repo happyskillsai/happycodex \
  --ref main \
  -f version=0.133.0 \
  -f npm_tag=latest \
  -f dry_run=false \
  -f provenance=true
```

Replace `0.133.0` with the release version.

### 4.2 Reusing Existing Native Artifacts

Use the publish-only workflow when the native build already succeeded:

```bash
gh workflow run happycodex-npm-publish.yml \
  --repo happyskillsai/happycodex \
  --ref main \
  -f version=0.133.0 \
  -f workflow_url=https://github.com/happyskillsai/happycodex/actions/runs/26362610179 \
  -f npm_tag=latest \
  -f dry_run=true \
  -f provenance=true
```

If the dry run succeeds, run:

```bash
gh workflow run happycodex-npm-publish.yml \
  --repo happyskillsai/happycodex \
  --ref main \
  -f version=0.133.0 \
  -f workflow_url=https://github.com/happyskillsai/happycodex/actions/runs/26362610179 \
  -f npm_tag=latest \
  -f dry_run=false \
  -f provenance=true
```

This workflow stages from the native artifacts in `workflow_url`.

### 4.3 Verification Commands

Check workflow status:

```bash
gh run view RUN_ID \
  --repo happyskillsai/happycodex \
  --json status,conclusion,jobs,url
```

Check npm metadata:

```bash
npm view @happyskillsai/happycodex version dist-tags bin optionalDependencies --json
```

Expected root metadata includes:

```json
{
  "version": "0.133.0",
  "bin": {
    "happycodex": "bin/codex.js"
  }
}
```

### 4.4 Install Smoke Test

Use a clean temp environment when possible:

```bash
npm install -g @happyskillsai/happycodex
happycodex --version
happycodex --help
```

If testing on the same machine as development work, be careful about existing global `codex` or `happycodex` commands in `PATH`.

## 5. Versioning Policy

### 5.1 Stable Upstream-Aligned Versions

When HappyCodex is based on upstream Codex `X.Y.Z` and includes only the standard HappyCodex downstream patch set, publish:

```text
@happyskillsai/happycodex@X.Y.Z
```

This makes it easy to know which upstream release a HappyCodex release tracks.

### 5.2 Downstream-Only Fix Versions

If HappyCodex needs a downstream-only fix before upstream publishes a newer version, publish prerelease-style versions:

```text
X.Y.Z-happy.1
X.Y.Z-happy.2
```

Use a non-`latest` npm tag for experimental or prerelease builds unless the release should become the recommended stable install.

### 5.3 Platform Variant Versions

The platform variants are automatically versioned as:

```text
X.Y.Z-linux-x64
X.Y.Z-linux-arm64
X.Y.Z-darwin-x64
X.Y.Z-darwin-arm64
X.Y.Z-win32-x64
X.Y.Z-win32-arm64
```

These are implementation details of the optional dependency model.

Do not install platform variants directly. Users install the root package:

```bash
npm install -g @happyskillsai/happycodex
```

## 6. Problems We Hit

### 6.1 Upstream Actions Were Noisy in the Fork

The upstream repository includes workflows designed for OpenAI's infrastructure.

In the fork, those workflows produced noisy failure emails because they expected:

- upstream secrets,
- upstream private runners,
- upstream release assumptions,
- upstream repository state.

We handled this by making heavy inherited workflows manual-only where appropriate and using HappyCodex-owned release workflows for npm publishing.

### 6.2 Native Release Builds Were Too Heavy

The inherited Rust release profile used:

```toml
lto = "fat"
codegen-units = 1
```

That is expensive on standard public GitHub-hosted runners.

The failed dry run showed symptoms like:

```text
runner shutdown signal
exit code 143
jobs cancelled around timeout
```

The fix was to harden `.github/workflows/happycodex-release.yml`:

```yaml
timeout-minutes: 240
env:
  CARGO_INCREMENTAL: "0"
  CARGO_PROFILE_RELEASE_CODEGEN_UNITS: "16"
  CARGO_PROFILE_RELEASE_LTO: thin
  CARGO_TERM_COLOR: always
```

We also added Cargo cache restore/save around the native build.

### 6.3 Linux musl Builds Needed Upstream-Specific Setup

Linux musl builds initially failed with UBSan-related linker/runtime errors, including undefined sanitizer symbols.

The release workflow now includes:

- Linux dependencies: `zstd`, `pkg-config`, `libcap-dev`, `libubsan1`,
- Zig setup for musl builds,
- `.github/scripts/install-musl-build-tools.sh`,
- `.github/actions/setup-rusty-v8-musl`,
- a `rustc` UBSan wrapper for Linux,
- sanitizer flag clearing for Linux.

These pieces are not incidental. Removing them can break musl release builds.

### 6.4 npm Rejected the Unscoped Name

The first real publish tried to publish:

```text
happycodex
```

npm rejected it:

```text
403 Forbidden - Package name too similar to existing package happy-codex
```

The fix was to publish under the npm organization scope:

```text
@happyskillsai/happycodex
```

The global command remains:

```text
happycodex
```

### 6.5 Publishing Must Be Platform-First

The platform variants must be published before the root package.

The root package contains optional dependencies pointing at exact platform variant versions. If the root package were published first, users could install a root package whose native dependency versions do not exist yet.

The workflows publish in this order:

1. `linux-x64`
2. `linux-arm64`
3. `darwin-x64`
4. `darwin-arm64`
5. `win32-x64`
6. `win32-arm64`
7. root package with `latest`

## 7. Key Ingredients That Made It Work

### 7.1 Keep Upstream Internals Where Possible

We minimized divergence from upstream by keeping:

- internal package keys such as `codex` and `codex-linux-x64`,
- tarball names such as `codex-npm-linux-x64-<version>.tgz`,
- JavaScript launcher path `bin/codex.js`,
- native binary name `codex`,
- native package archive layout.

This reduces future merge conflicts.

### 7.2 Scope Only the Published Package Name

The correct final identity split is:

```text
npm package: @happyskillsai/happycodex
global command: happycodex
native binary: codex
internal launcher file: bin/codex.js
```

This looks odd at first, but it is the lowest-risk shape for a downstream fork.

### 7.3 Validate Tarballs Before Publishing

The workflows inspect every staged tarball before publishing.

They verify:

- every tarball exists,
- every package has name `@happyskillsai/happycodex`,
- the root package exposes `bin.happycodex`,
- the root optional dependencies point to `npm:@happyskillsai/happycodex@...`.

This catches package identity regressions before npm receives anything.

### 7.4 Use GitHub Actions for Native Releases

Do not publish native HappyCodex releases manually from a laptop.

Manual local publish is risky because the full release contains six platform-native packages. GitHub Actions gives:

- Linux x64 native build,
- Linux ARM64 native build,
- macOS x64 native build,
- macOS ARM64 native build,
- Windows x64 native build,
- Windows ARM64 native build,
- provenance,
- repeatable logs,
- artifacts for retry.

### 7.5 Keep Dry Runs Mandatory Before Real Publish

The dry run caught the scoped package metadata path before the real scoped publish.

The required pattern is:

1. dry run first,
2. inspect workflow success,
3. real publish second,
4. verify npm registry metadata.

## 8. Important Files

### 8.1 Package Metadata

```text
codex-cli/package.json
```

Important fields:

- `name`: `@happyskillsai/happycodex`
- `bin.happycodex`: `bin/codex.js`
- `repository.url`: `git+https://github.com/happyskillsai/happycodex.git`

### 8.2 npm Staging Code

```text
codex-cli/scripts/build_npm_package.py
```

Important constants:

- `CODEX_NPM_NAME = "@happyskillsai/happycodex"`
- `CODEX_PLATFORM_PACKAGES[*].npm_name = "happycodex-*"`

The `npm_name` values are local optional dependency aliases. The actual package published to npm is `@happyskillsai/happycodex`.

### 8.3 npm Launcher

```text
codex-cli/bin/codex.js
```

Important responsibilities:

- maps current OS and CPU to a native target triple,
- resolves the installed optional native package,
- falls back to local `vendor` layout when running from a staged package,
- spawns the native `codex` binary,
- prints reinstall advice using `@happyskillsai/happycodex`.

### 8.4 Release Workflows

```text
.github/workflows/happycodex-release.yml
.github/workflows/happycodex-npm-publish.yml
```

`happycodex-release.yml` builds native artifacts and publishes.

`happycodex-npm-publish.yml` reuses existing native artifacts and publishes only npm packages.

### 8.5 Documentation

```text
FORKING.md
HAPPYCODEX_NPM_RELEASE.md
README.md
```

`FORKING.md` explains the broader fork and feature changes.

`HAPPYCODEX_NPM_RELEASE.md` is the release operations runbook.

`README.md` contains the user-facing install command.

## 9. Production Release Record

### 9.1 Failed Unscoped Publish

Run:

```text
https://github.com/happyskillsai/happycodex/actions/runs/26362610179
```

What succeeded:

- all six native builds,
- native artifact uploads,
- npm tarball staging,
- metadata validation.

What failed:

```text
npm publish dist/npm/codex-npm-linux-x64-0.133.0.tgz --tag linux-x64 --access public --provenance
```

npm returned:

```text
403 Forbidden - Package name too similar to existing package happy-codex
```

Resolution:

- changed package name from `happycodex` to `@happyskillsai/happycodex`,
- kept global command `happycodex`,
- reused the already-built native artifacts with `happycodex-npm-publish.yml`.

### 9.2 Successful Scoped Publish

Scoped dry run:

```text
https://github.com/happyskillsai/happycodex/actions/runs/26380428109
```

Real scoped publish:

```text
https://github.com/happyskillsai/happycodex/actions/runs/26380795664
```

Verification command:

```bash
npm view @happyskillsai/happycodex version dist-tags bin optionalDependencies --json
```

Verified output included:

```json
{
  "version": "0.133.0",
  "dist-tags": {
    "latest": "0.133.0",
    "linux-x64": "0.133.0-linux-x64",
    "linux-arm64": "0.133.0-linux-arm64",
    "darwin-x64": "0.133.0-darwin-x64",
    "darwin-arm64": "0.133.0-darwin-arm64",
    "win32-x64": "0.133.0-win32-x64",
    "win32-arm64": "0.133.0-win32-arm64"
  },
  "bin": {
    "happycodex": "bin/codex.js"
  }
}
```

## 10. Troubleshooting

### 10.1 npm 403 Similar Package Name

Symptom:

```text
403 Forbidden - Package name too similar to existing package
```

Cause:

npm blocks some unscoped names that are too close to existing packages.

Fix:

Use the scoped package:

```text
@happyskillsai/happycodex
```

Do not go back to unscoped `happycodex` unless npm policy changes and the migration is intentional.

### 10.2 npm 404 Before First Publish

Symptom:

```text
npm view @happyskillsai/happycodex
404 Not Found
```

Cause:

Before first publish, this is expected.

After production publish, this should not happen for public npm registry access.

### 10.3 Cargo Build Timeout or Runner Shutdown

Symptoms:

```text
runner shutdown signal
exit code 143
job cancelled near timeout
```

Likely cause:

Release build too expensive for the runner settings.

Check:

- `timeout-minutes` is still `240`,
- `CARGO_PROFILE_RELEASE_LTO` is still `thin`,
- `CARGO_PROFILE_RELEASE_CODEGEN_UNITS` is still `16`,
- Cargo cache restore/save is still present,
- upstream merge did not revert release env overrides.

### 10.4 Missing Optional Dependency After Install

Symptom:

```text
Missing optional dependency happycodex-darwin-arm64
```

Likely causes:

- npm skipped optional dependencies,
- platform variant was not published,
- root package points to wrong optional dependency versions,
- package manager cache is stale.

Check:

```bash
npm view @happyskillsai/happycodex optionalDependencies --json
```

Then reinstall:

```bash
npm install -g @happyskillsai/happycodex
```

### 10.5 Partial Publish Risk

npm publishes are not transactional across multiple package versions.

If a platform variant publishes and a later publish fails, npm may contain a partial set.

The workflow reduces this risk by:

- dry-running first,
- validating all tarballs first,
- publishing root last.

If a partial publish happens, do not blindly rerun a workflow that republishes already-published versions unless npm accepts idempotent behavior for the exact scenario. Usually the fix is to bump to a new patch or downstream prerelease version.

## 11. Future Maintenance Rules

### 11.1 Before Merging Upstream

Check that upstream changes did not overwrite:

- `codex-cli/package.json` package name and bin map,
- `codex-cli/scripts/build_npm_package.py` `CODEX_NPM_NAME`,
- `codex-cli/bin/codex.js` platform alias names and reinstall command,
- HappyCodex release workflows,
- `scripts/stage_npm_packages.py` artifact repository behavior.

### 11.2 Before Releasing

Always confirm:

```bash
git status --short --branch
npm view @openai/codex version
npm view @happyskillsai/happycodex version dist-tags --json
```

Then run dry run before real publish.

### 11.3 When Changing Package Names

Package identity appears in multiple places:

- npm metadata,
- staging script constants,
- workflow validation,
- launcher reinstall message,
- README install command,
- fork documentation,
- optional dependency target strings.

Do not change only `codex-cli/package.json`. A package-name change must be coordinated across all release and verification paths.
