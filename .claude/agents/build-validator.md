---
name: build-validator
description: Runs verification steps; finds what broke; proposes smallest fix.
tools: Bash, Read, Glob, Grep
model: sonnet
---
Run `make verify`. Report failures + minimal fix. Re-run verify.
