# Contributing

Thanks for your interest in contributing to `ha-tibber-vehicle`! Contributions
are welcome. To keep collaboration smooth, please follow these guidelines.

## How to contribute

1. **Fork the repository** and create a clearly named feature branch (e.g.,
   `fix/soc-unit-conversion` or `feat/multi-vehicle-support`).
2. **Write clear commit messages** following [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `chore:` for dependency bumps, version bumps, and similar housekeeping
   - `refactor:` for code refactoring
3. **Keep the docs in sync** — see [`CLAUDE.md`](CLAUDE.md)'s file table for
   exactly which of `README.md`/`docs/DEVELOPMENT.md`/`docs/DECISIONS.md`/
   `docs/CONTEXT.md`/`CHANGELOG.md` a given change touches. They have
   distinct audiences (end user vs. developer vs. "why does this exist") —
   not just "update everything the same way".
4. **Open a Pull Request** with a clear description of what changed and why.

## Development setup

```bash
git clone https://github.com/YOUR_USERNAME/ha-tibber-vehicle.git
cd ha-tibber-vehicle
```

From there, see [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for the actual
local dev loop (disposable Dockerized HA instance) and unit test setup —
not repeated here to avoid the two drifting out of sync.

## Project-specific notes

This is a standalone Home Assistant integration reading vehicle data from
Tibber's official Data API — it is **not** a fork or extension of
`homeassistant-volkswagencarnet`, and **not** a connector for Till
Steinbach's `carconnectivity` ecosystem. See
[`docs/DECISIONS.md`](docs/DECISIONS.md) for why, before proposing a change
that would couple this project to either. The Tibber Data API is confirmed
read-only (state of charge, target SoC, range, plug/charging status only) —
see [`docs/CONTEXT.md`](docs/CONTEXT.md) §3 before assuming otherwise or
proposing control/write features this API cannot support.

## Code style

- Follow the conventions already in the file you're editing.
- Add type hints for new function parameters and return values.
- Default to no comments; where one is genuinely needed, it should explain
  *why*, not *what* — see the project's general engineering conventions.
- Keep sensor/coordinator logic mapped directly to the Tibber capability
  ids documented in `docs/CONTEXT.md` — avoid adding abstraction layers not
  required by Home Assistant's own entity model.

## Reporting issues

- **Search existing issues** before opening a new one.
- **Provide clear reproduction steps** with expected vs. actual behavior.
- **Include your environment**: Home Assistant version, this integration's
  version, and whether you're on the disposable dev instance or a real HA
  installation.
- **Attach relevant logs** from Home Assistant's own log viewer.

## Questions?

Check [`README.md`](README.md) first — installation and setup are
documented there. For background on *why* this project exists and how it
relates to other projects, see [`docs/CONTEXT.md`](docs/CONTEXT.md). For
anything else, open an issue.

## License

By contributing, you agree that your contributions will be licensed under
the [MIT License](LICENSE).
