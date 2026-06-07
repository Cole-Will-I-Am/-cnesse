# Changelog

_Auto-generated every cycle from the audit chain. Newest first._

## 2026-06-07T09:05:45+00:00 · `db0a0a1ee652` · **rejected**
- 
- _why:_ coder produced no valid change

## 2026-06-07T08:43:47+00:00 · `12822b72c514` · **merged** · score 0.92
- Add ecnyss/util/graphs.py with has_cycle and topological_sort DAG primitives, plus tests/test_graphs.py with 19 pure-logic unit tests
- _why:_ approved (score 0.9146 >= 0.0+0.6) | goal: **Goal:** Add `ecnyss/util/graphs.py` — pure-stdlib DAG primitives (`topological_sort`, `has_cycle`) with companion `tes

## 2026-06-07T08:25:50+00:00 · `631a92604275` · **merged** · score 0.88
- Added ecnyss/util/numbers.py with 7 pure-stdlib numeric primitives (clamp, sign, lerp, normalize, remap, round_to, is_close) and comprehensive unit tests in ecnyss/util/test_numbers.py. Updated ecnyss/util/__init__.py to export new functions. All 28 test cases cover edge cases and error handling.
- _why:_ approved (score 0.8905 >= 0.0+0.6) | goal: **Goal:** Add `ecnyss/util/numbers.py` with pure-stdlib numeric primitives (clamp, sign, lerp, normalize, remap, round_t

## 2026-06-07T08:05:41+00:00 · `58b06cb29600` · **merged** · score 0.87
- Created ecnyss/util/itertools.py with 4 pure-stdlib iterator utilities (batched, pairwise, sliding_window, consume) and tests/test_itertools.py with comprehensive unit tests for each function following the established pattern of util/collections.py and util/functional.py.
- _why:_ approved (score 0.92 >= 0.0+0.6) | goal: 

## 2026-06-07T07:43:31+00:00 · `d6ef9ca34485` · **merged** · score 0.93
- Added Result monad module (ecnyss/util/results.py) with Ok/Err variants, map/bind operations, and comprehensive unit tests (tests/test_results.py). Updated ecnyss/util/__init__.py to export Result types. Pure stdlib implementation with frozen dataclasses and Python 3.12+ type syntax.
- _why:_ approved (score 0.92 >= 0.0+0.6) | goal: **Goal:** Add `ecnyss/util/results.py` — a pure-stdlib `Result[T, E]` monad (`Ok`, `Err`, `map`, `bind`, `unwrap_or`, `i

## 2026-06-07T07:25:47+00:00 · `de879f4dd0e7` · **merged** · score 0.92
- Created ecnyss/util/functional.py with 7 pure-stdlib functional utilities (identity, constant, compose, pipe, curry, partial, flip) and tests/test_functional.py with comprehensive unit tests for all functions.
- _why:_ approved (score 0.9519 >= 0.0+0.6) | goal: 

## 2026-06-07T07:03:17+00:00 · `43ae52cfafec` · **merged** · score 0.75
- Created ecnyss/util/diff.py with deep_equal and deep_diff functions, plus ecnyss/util/test_diff.py with comprehensive unit tests. Both files are pure stdlib, no I/O, following the pattern of dicts.py/test_dicts.py.
- _why:_ approved (score 0.8082 >= 0.0+0.6) | goal: **Goal:** Add `ecnyss/util/diff.py` — pure-stdlib structural diff utilities (`deep_diff`, `deep_equal`) for nested dicts

## 2026-06-07T06:44:30+00:00 · `8bbb59f87e33` · **merged** · score 0.89
- Created ecnyss/util/trees.py with get_in, set_in, update_in, walk functions and ecnyss/util/test_trees.py with 12 pure-logic unit tests
- _why:_ approved (score 0.8915 >= 0.0+0.6) | goal: **Goal:** Add `ecnyss/util/trees.py` with pure-stdlib nested-structure utilities (`get_in`, `set_in`, `update_in`, `walk

## 2026-06-07T06:23:58+00:00 · `45fe874da00d` · **rejected** · score 0.38
- Created ecnyss/util/iterables.py with 4 pure-stdlib utilities (partition, group_by, first, windowed) and tests/test_iterables.py with comprehensive unit tests following existing patterns.
- _why:_ sandbox tests failed | goal: 

## 2026-06-07T06:03:49+00:00 · `f58313207a82` · **rejected** · score 0.74
- Created ecnyss/util/validation.py with 4 pure-stdlib validation utilities (is_email, is_url, is_uuid, is_semver) and comprehensive unit tests in tests/test_validation.py. All functions use only stdlib (re, uuid), no I/O, no external dependencies.
- _why:_ red team BLOCK | goal: 

## 2026-06-07T05:44:04+00:00 · `36fba1f38593` · **rejected** · score 0.35
- Created ecnyss/util/strings.py with 5 pure string utility functions (slugify, truncate, word_count, camel_to_snake, snake_to_camel) and tests/test_strings.py with comprehensive unit tests for each function class. All code is pure-stdlib, no I/O/network/subprocess, compatible with locked-down test ja
- _why:_ sandbox tests failed | goal: 

## 2026-06-07T05:24:13+00:00 · `2d5a84de4680` · **merged** · score 0.9
- Created ecnyss/util/dicts.py with 4 pure-stdlib dictionary utilities (deep_merge, pick, omit, flatten_keys) and ecnyss/util/test_dicts.py with 20 unit tests covering all functions
- _why:_ approved (score 0.8973 >= 0.0+0.6) | goal: **Goal:** Add `ecnyss/util/dicts.py` — a self-contained, pure-stdlib dictionary utility module providing `deep_merge`, `

## 2026-06-07T05:15:56+00:00 · `55c30cbfba49` · **merged** · score 0.85
- Created ecnyss.util package with pure-stdlib collection utilities (chunk, flatten, unique_preserve_order, take) and comprehensive unit tests covering normal cases, edge cases, and iterator inputs.
- _why:_ approved (score 0.8701 >= 0.0+0.6) | goal: 

## 2026-06-07T05:10:07+00:00 · `db98186c2c5e` · **rejected** · score 0.6
- Created ecnyss/text_utils.py with 4 pure text utilities (slugify, truncate, word_count, line_count) and tests/test_text_utils.py with comprehensive unit tests. All stdlib-only, no I/O, no external deps.
- _why:_ sandbox tests failed | goal: 

## 2026-06-07T05:04:06+00:00 · `55f0d95692f3` · **rejected** · score 0.41
- Created ecnyss/analysis module with pure-stdlib Python code analysis capabilities and comprehensive unit tests. Module provides parse_source, extract_functions, extract_classes, and count_lines with dataclass results. Tests cover valid/invalid parsing, function extraction with args/docstrings/return
- _why:_ sandbox tests failed | goal: 

## 2026-06-07T04:56:01+00:00 · `508f864ee249` · **rejected** · score 0.57
- Created new ecnyss/metrics module with pure-stdlib code analysis capabilities including line counting, complexity estimation, and structural metrics. Added comprehensive unit tests covering all specified scenarios.
- _why:_ sandbox tests failed | goal: 

## 2026-06-07T04:43:03+00:00 · `7f3f9473fedc` · **rejected** · score 0.28
- Created comprehensive test suite for sandbox.py to identify failure modes causing spurious rejections. Tests cover initialization, evaluate method, path safety checks, test command construction, test execution, and specific spurious rejection scenarios including nested directories, unicode content,
- _why:_ sandbox tests failed | goal: **Goal:** Harden `ecnyss/kernel/sandbox.py` to reliably execute tests for all kernel and protocol modules without spurio

## 2026-06-07T04:28:23+00:00 · `153419f8c5b2` · **rejected** · score 0.7
- Created SelfModel and WorldModel classes in ecnyss/kernel/self_world.py with dataclass implementations, and created comprehensive test suite in tests/test_self_world.py covering instantiation, field integrity, type distinction, and core identity validation.
- _why:_ sandbox tests failed | goal: **Goal:** Add minimal deterministic unit tests for `kernel.self_world` (`SelfModel`, `WorldModel`) covering instantiatio

## 2026-06-07T04:21:27+00:00 · `003f7a7a1a21` · **rejected** · score 0.75
- Created tests/test_hash_chain.py with 3 deterministic unit tests covering: (1) append correctly links prev_hash, (2) verify_chain validates intact chains, (3) verify_chain detects tampering (modified payload, broken prev_hash, index mismatch). Uses tempfile for isolation, follows test_sandbox.py pat
- _why:_ sandbox tests failed | goal: **Goal:** Add deterministic unit tests for `protocol.hash_chain` covering append, link verification, and tamper detectio

## 2026-06-07T04:01:38+00:00 · `d7410b7fa905` · **merged** · score 0.92
- Created tests/test_sandbox.py with 3 deterministic tests covering valid execution, syntax errors, and runtime errors. Each test sets up an isolated git repo, exercises the Sandbox.evaluate() API, and verifies the report structure.
- _why:_ approved (score 0.92 >= 0.0+0.0) | goal: Goal: Add minimal deterministic tests for `kernel.sandbox` that verify it can execute valid code and surface errors, est

## 2026-06-07T03:43:15+00:00 · `fe9cbf46af76` · **merged** · score 0.85
- Added validate_canonical_form function to canonical.py and corresponding test in test_protocol.py
- _why:_ approved (score 0.875 >= 0.0+0.0) | goal: 

## 2026-06-07T03:21:38+00:00 · `4c7b5917075c` · **rejected** · score 0.58
- Created tests/test_permission_model.py with 7 minimal unit tests for grant/deny matrix and boundary checks.
- _why:_ sandbox tests failed | goal: **Goal:** Add minimal, focused unit tests for `kernel.permission_model` covering only the capability grant/deny decision

## 2026-06-07T03:11:10+00:00 · `9fc0677242a1` · **rejected** · score 0.75
- Created tests/test_kernel.py with comprehensive unit tests for kernel.permission_model and kernel.sandbox modules. Tests cover capability grant/deny, boundary enforcement, isolation guarantees, state leakage prevention, and concurrent access safety using pytest fixtures.
- _why:_ sandbox tests failed | goal: Goal: Unit-test `kernel.permission_model` and `kernel.sandbox` boundary contracts (isolation, capability checks, and sta

## 2026-06-07T03:01:59+00:00 · `cfae90b81954` · **pending**
- second cycle
- _why:_ confirm chain links

## 2026-06-07T03:01:59+00:00 · `10d0830f3de7` · **pending**
- bootstrap audit spine
- _why:_ prove the chain records before any mutation

