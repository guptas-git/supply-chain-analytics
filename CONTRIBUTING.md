# Contributing

Bug reports, documentation fixes and small, well-tested analytical functions are welcome.

## Development

Fork the repository, clone your fork and create a feature branch. Use Python 3.10 or newer and a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -v
python examples/inventory_basics.py
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` in PowerShell.

Keep changes focused. Document assumptions and units in public functions, include tests for normal and invalid inputs, and update the README and changelog when behavior changes. Submit a pull request with the problem, the change and the checks you ran.

The inventory package has no runtime dependencies. The PostgreSQL pipeline and Tableau workbook are separate examples; their setup is documented in the README and `dashboard/README.md`.

## Reporting issues

Include a small reproducible example, expected and actual behavior, Python version and package version. Use synthetic or appropriately licensed data. Do not attach credentials or confidential business records.

## Licensing

Contributions to the original software are accepted under the repository's MIT License. Third-party datasets and data-derived dashboard assets retain their existing licenses; do not submit data without permission to redistribute it.
