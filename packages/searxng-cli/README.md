# ghostship-searxng

`ghostship-searxng` is the first repo-local Python utility packaged for `ghostship-hermes`.

## Contract

- executable name: `ghostship-searxng`
- Python package name: `ghostship-searxng`
- import package: `ghostship_searxng`
- CLI shape: `ghostship-searxng search web <query> [flags]`
- machine-readable mode: `--json`

## Development

Lock dependencies:

```fish
python3 ../../scripts/python_utility.py lock .
```

Run tests:

```fish
python3 ../../scripts/python_utility.py test .
```

Build wheel and sdist:

```fish
python3 ../../scripts/python_utility.py build .
```

## Integration Testing

Set `SEARXNG_BASE_URL` to enable the live integration test.
