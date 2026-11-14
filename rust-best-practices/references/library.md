# Published libraries

Read this file only for a crate that other people depend on, such as one published to crates.io or shared across teams. Application code skips it. These rules matter here because a library's public API can't change without breaking its users.

| ID | Rule |
|----|------|
| L1 | **Keep the public surface small.** Every `pub` item is a promise. Export one path per item. Don't use glob re-exports. |
| L2 | **Keep wrappers and other crates' types out of the API.** Don't return `Rc`, `Arc`, `RefCell`, or `Box<dyn ...>`, and don't expose a dependency's types. Each one ties your semver to theirs, or to your internals. |
| L3 | **Public types derive `Debug`. Public types and futures are `Send`** unless they have a stated reason not to be. Check this at compile time: `const _: fn() = || { fn is_send<T: Send>() {} is_send::<MyType>(); };`. |
| L4 | **Doc sections where they apply.** `# Errors` on every fallible function, `# Panics` on every function that can panic, `# Safety` on every `unsafe fn`. Write examples with `?`, not `unwrap`. |
| L5 | **Use `#[non_exhaustive]`** only on a public enum or struct that you expect to grow. It makes callers add a `_ =>` arm, so it gives up T5 for them. |
| L6 | **Features only add.** Turning a feature on never removes an API. Name a `std` feature rather than a `no-std` one. Set `rust-version` in `Cargo.toml` and raise it rarely. |
| L7 | **Check semver before a release.** Run `cargo semver-checks`. It catches most breakage, but not all of it. |
