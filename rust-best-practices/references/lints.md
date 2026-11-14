# Lint config

This config enforces the **lint** rules in `SKILL.md`. It is a short, chosen list rather than the whole `pedantic` group, because noise teaches people to ignore warnings. Offer it to the user when the repo has no `[lints]` table yet. Don't add it to the repo yourself.

The `[lints]` table needs Rust 1.74 or later. `#[expect]` needs Rust 1.81 or later.

## `Cargo.toml`

In a workspace, put the table under `[workspace.lints]` and add `[lints] workspace = true` to each member crate.

```toml
[lints.rust]
unsafe_op_in_unsafe_fn = "deny"      # U1
unreachable_pub = "warn"             # O3
redundant_lifetimes = "warn"         # O6

[lints.clippy]
# E1: no panics on input
unwrap_used = "deny"
indexing_slicing = "warn"
string_slice = "warn"
# E3: no placeholders
todo = "deny"
unimplemented = "deny"
dbg_macro = "deny"
# T5: exhaustive match
wildcard_enum_match_arm = "warn"
# T6: numbers convert explicitly
as_conversions = "warn"
cast_possible_truncation = "warn"
cast_sign_loss = "warn"
cast_possible_wrap = "warn"
# T1: flag bags
fn_params_excessive_bools = "warn"
struct_excessive_bools = "warn"
# U1: documented unsafe
undocumented_unsafe_blocks = "deny"
multiple_unsafe_ops_per_block = "warn"
# Q1: overrides carry a reason
allow_attributes = "warn"
allow_attributes_without_reason = "warn"
# Q3: no stray prints (a CLI's real output uses #[expect] with a reason)
print_stdout = "warn"
print_stderr = "warn"
```

These are on by default and need no config: `ptr_arg` (O1), `needless_range_loop` and `needless_lifetimes` (O6), `await_holding_lock` (A2), `too_many_arguments` (O5, tuned below).

## `clippy.toml`

```toml
too-many-arguments-threshold = 3   # O5: more than 3 parameters is flagged
allow-unwrap-in-tests = true
allow-expect-in-tests = true
allow-indexing-slicing-in-tests = true
allow-panic-in-tests = true
allow-print-in-tests = true
allow-dbg-in-tests = true
```

## Notes

- `Mutex::lock()` returns an `Err` only when a thread panicked while holding the lock. Use `.expect("lock poisoned")` there. `unwrap_used` stays strict, and the message says why the expect holds.
- Keep `-D warnings` on the command line and in CI. Don't put `#![deny(warnings)]` in the source, because a new compiler release would then break the build.
- Leave `expect_used` off: E1 allows `expect` for invariants. Leave the whole `restriction` group off: its lints contradict each other.
