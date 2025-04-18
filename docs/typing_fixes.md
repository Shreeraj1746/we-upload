# Python Typing Improvements

## Background

The project currently targets Python 3.9, where `typing.Union` and `typing.Optional` are used for type hints.
For Python 3.10+, these can be replaced with more concise syntax like `X | Y` and `X | None`.

Additionally, when using `typing.Union` and `typing.Optional` with forward references in Python 3.9,
the code should include `from __future__ import annotations` to avoid evaluation issues.

## Current Status

We've temporarily disabled the following rules in the Ruff linter:

- `FA100`: Missing `from __future__ import annotations`, but uses `typing.Union`/`typing.Optional`
- `UP007`: Use `X | Y` for type annotations
- `UP038`: Use `X | Y` in `isinstance` call instead of `(X, Y)`

## Action Plan

1. **Short-term Solution**:
   - Continue with disabled linting rules to maintain a passing CI pipeline

2. **Medium-term Solution**:
   - Add `from __future__ import annotations` to all files using forward references
   - This will resolve the FA100 warnings while still supporting Python 3.9

3. **Long-term Solution**:
   - When migrating to Python 3.10+:
     - Replace `typing.Union[X, Y]` with `X | Y`
     - Replace `typing.Optional[X]` with `X | None`
     - Replace `isinstance(x, (A, B))` with `isinstance(x, A | B)`
     - Remove the `from __future__ import annotations` imports (as they'd be redundant)

## Files Needing Fixes

The following files need the `from __future__ import annotations` import:

- app/core/config.py
- app/core/security.py
- app/schemas/file.py
- app/schemas/token.py
- app/schemas/user.py
- app/services/file_service.py
- app/services/user_service.py

## Implementation Priority

1. Fix type annotations in core modules first (app/core/*)
2. Fix schemas (app/schemas/*)
3. Fix services (app/services/*)

This progression ensures the most critical components are fixed first while following the dependency chain.
