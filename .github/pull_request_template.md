## Summary

- change:
- reason:

## Verification

- [ ] `cd packages/hermes-dashboard && uv run --extra dev python -m pytest tests -q -s`
- [ ] `uvx --from pytest pytest tests/hermes-image/test_discord_thread_contract_static.py -q -s`
- [ ] `docker build --target final --build-arg HERMES_REF="$(tr -d '\n' < packages/hermes-image/hermes-release.txt)" --tag ghostship-hermes:ci --file packages/hermes-image/Dockerfile .`
- [ ] `tests/hermes-image/single-agent-dashboard.sh ghostship-hermes:ci`
