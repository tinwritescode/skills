---
name: rust-best-practices
description: Opinionated Rust rules for the smallest code that keeps working as it grows. Types make bad states unbuildable, input is parsed once, errors are typed, and nothing is added before it is needed. Use when writing, editing, or reviewing Rust code.
paths: ["**/*.rs", "**/Cargo.toml"]
---

# Rust best practices

These rules are opinionated. They follow no company's style guide. They aim at one thing: **the smallest code that still scales**, where scaling means a new feature or a new teammate changes one place and the compiler points at every other place that must follow.

The golden rule: add a type, trait, generic, crate, or layer only when the code in front of you needs it now. If a rule below would add more code than the bug it prevents, skip that rule. When it is a close call, choose the simpler option.

The repo's own `AGENTS.md`, `CLAUDE.md`, and lint config win over this file.

**How to use these rules.** Follow them while you write. When you review, cite a rule's ID (`T2`, `E1`). The *Check* column says how each rule is enforced:

- **lint**: the lint config in [`references/lints.md`](references/lints.md) catches it.
- **review**: no lint can catch it, so read the diff for it. Bad and good examples are in [`references/patterns.md`](references/patterns.md).

If the crate is published for other people to depend on, also read [`references/library.md`](references/library.md).

## Simple

| ID | Rule | Check |
|----|------|-------|
| S1 | **No speculative abstraction.** Write a trait when two types implement it today, and a generic when two types use it today. Use a builder only when a struct literal is no longer readable. Until then, write a plain function and a plain struct. | review |
| S2 | **Flat modules by feature.** Group code by what it does (`billing/`, `auth/`), not by layer (`models/`, `services/`). Split a file when it no longer fits in your head, not to follow a pattern. | review |
| S3 | **Few dependencies.** Try std first, then a crate already in `Cargo.lock`. Add a new crate only when it replaces a lot of tricky code, and turn off the default features you don't use. | review |
| S4 | **Sync by default.** Use async only for I/O concurrency. A function that does no I/O is not `async`. | review |

## Types

| ID | Rule | Check |
|----|------|-------|
| T1 | **Enums over flag bags.** Model each state as an enum variant that carries its own data. Don't use a struct of `Option` fields and `bool` flags where only some combinations are valid. | review, lint for excess bools |
| T2 | **Newtypes for meaning.** `struct OrderId(Uuid)` has a private field and a checking constructor (`TryFrom`, `FromStr`, or `new() -> Result`), so holding one proves the check happened. Wrap a primitive only when mixing it up with another value is a real risk. | review |
| T3 | **Constructive types, only where needed.** Keep `Vec<T>`, `String`, and `u64` while every operation on them stays total. Switch to a type that can't hold the bad value (`NonZeroU32`, a head plus a `Vec`, typestate) only where the loose type forces an `unwrap`, an `expect`, or an `unreachable!`. | review |
| T4 | **Parse at the boundary.** Deserialize straight into domain types (`#[serde(try_from = "...")]`). Raw `serde_json::Value`, `HashMap<String, _>`, and `&str` from outside stop at that parse. Inside, trust the types. | review |
| T5 | **Exhaustive match.** Match your own enums without a `_ =>` arm, so adding a variant breaks every place that has to handle it. | lint |
| T6 | **Numbers convert explicitly.** Use `From` to widen and `TryFrom` to narrow, never `as`. Use `checked_` or `saturating_` arithmetic on values that come from input. Float to int: round first, then check the range. | lint |

## Errors

| ID | Rule | Check |
|----|------|-------|
| E1 | **Bad input returns `Result`; a bug panics.** `unwrap`, slice indexing, and `panic!` never touch data from outside: use `?`, `.get()`, or `let ... else`. A broken invariant the code itself guarantees uses `expect("why it holds: {value}")`. Panics are never used for control flow. | lint |
| E2 | **Typed errors.** A library module returns its own `thiserror` enum with one variant per failure a caller can act on. A binary uses `anyhow` and adds `.context()` at each layer. Write the `From` conversion once instead of a `map_err` at every call. Never `Result<T, String>`. | review |
| E3 | **No placeholders in committed code.** No `todo!`, `unimplemented!`, or `dbg!`. | lint |

## Ownership and API

| ID | Rule | Check |
|----|------|-------|
| O1 | **Borrow in, own out.** Take `&str`, `&[T]`, or `&Path`, never `&String` or `&Vec<T>`. Return owned values. Use `PathBuf` for paths, not `String`. | lint |
| O2 | **No clone to quiet the borrow checker.** A `.clone()` added only to make the code compile means the ownership is wrong, so restructure. A clone of an `Arc` or of a small value that you really need twice is fine. | review |
| O3 | **Smallest visibility.** Items are private by default, then `pub(crate)`, and `pub` only for what other crates call. | lint |
| O4 | **Standard traits over custom methods.** Implement `From`, `TryFrom`, `FromStr`, `Display`, and `Default` before writing `to_x()` or `parse_x()`. They work with `?`, `.into()`, `format!`, and serde for free. | review |
| O5 | **Struct args past three.** Rust has no named arguments. With more than three parameters, or two parameters of the same type side by side, pass one struct instead. | lint |
| O6 | **Iterators and elided lifetimes.** Use iterator chains instead of index loops. Write a lifetime only when the compiler asks for one. | lint |

## Async and shared state

| ID | Rule | Check |
|----|------|-------|
| A1 | **Own, don't share.** Pass ownership or send messages. Use `Arc<Mutex<T>>` only when two writers really need the same value. | review |
| A2 | **Use `std::sync::Mutex` for plain data**, with a short critical section, and never hold its guard across `.await`. Use the tokio `Mutex` only for an I/O resource that is held across an `.await`. | lint |
| A3 | **No blocking calls inside async code.** Blocking I/O goes in `spawn_blocking`. CPU-heavy work goes to a thread or to rayon. | review |

## Unsafe

| ID | Rule | Check |
|----|------|-------|
| U1 | **Don't write `unsafe`.** If you must, keep the block as small as possible, add a `// SAFETY:` comment that names the invariant and why it holds, and run `cargo +nightly miri test`. | lint |

## Quality

| ID | Rule | Check |
|----|------|-------|
| Q1 | **Lints stay clean.** `cargo fmt` and `cargo clippy --all-targets --all-features -- -D warnings` pass. Override a lint only with `#[expect(lint, reason = "...")]` on the narrowest item, never with a bare `#[allow]`. | lint |
| Q2 | **Tests run the real thing.** When a temp dir or a local database is cheap and deterministic, use it. Put the clock, the network, and randomness behind a small seam you can fake. Use `proptest` for parsers and round trips. A test that would still pass if the function returned `Default` is not a test. | review |
| Q3 | **Structured logs.** Use `tracing` with fields and a span that carries the request or job ID. No `println!` in shipped code, unless stdout is the CLI's real output. | lint |

## Done

Rust work is done when:

- `cargo fmt --check`, `cargo clippy --all-targets --all-features -- -D warnings`, and the tests of every touched crate pass.
- If the diff touches `unsafe`, `cargo +nightly miri test` passes. If the repo has a `deny.toml`, `cargo deny check` passes.
- Every **review** rule has been checked against the diff. Every `unwrap`, `expect`, `as`, `.clone()`, `#[expect]`, and `unsafe` the diff adds names the rule that allows it.
- If the repo has no `[lints]` table, you offered the user the config in `references/lints.md` instead of adding it yourself.
