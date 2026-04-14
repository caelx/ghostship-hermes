## Summary

- change:
- reason:

## Verification

- [ ] `python3 scripts/python_utility.py lock packages/searxng-cli`
- [ ] `python3 scripts/python_utility.py test packages/searxng-cli`
- [ ] `python3 scripts/python_utility.py build packages/searxng-cli`
- [ ] `docker build --target final --build-arg HERMES_REF="$(tr -d '\n' < packages/hermes-image/hermes-release.txt)" --tag ghostship-hermes:ci --file packages/hermes-image/Dockerfile .`
- [ ] `tests/hermes-image/single-agent-dashboard.sh ghostship-hermes:ci`
