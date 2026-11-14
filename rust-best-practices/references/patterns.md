# Patterns

Bad and good examples for the **review** rules in `SKILL.md`. Each pair is the smallest code that shows the difference. S2 and S3 have no code, because the rule itself is the whole check.

## S1: No speculative abstraction

```rust
// Bad: a trait with one implementation, written "for later".
trait Notifier { fn send(&self, msg: &str) -> Result<(), Error>; }
struct EmailNotifier { client: Smtp }
impl Notifier for EmailNotifier { /* ... */ }
fn alert(n: &dyn Notifier, msg: &str) -> Result<(), Error> { n.send(msg) }

// Good: one type, one function. Add the trait when a second notifier exists.
struct Email { client: Smtp }
impl Email { fn send(&self, msg: &str) -> Result<(), Error> { /* ... */ } }
```

## S4: Sync by default

```rust
// Bad: async with nothing to await. Every caller now needs a runtime.
async fn total(items: &[Item]) -> Money { items.iter().map(|i| i.price).sum() }

// Good
fn total(items: &[Item]) -> Money { items.iter().map(|i| i.price).sum() }
```

## T1: Enums over flag bags

```rust
// Bad: 4 fields, 16 combinations, 3 of them valid.
struct Payment { paid: bool, refunded: bool, paid_at: Option<Time>, reason: Option<String> }

// Good: each variant holds only the data it can have.
enum Payment {
    Pending,
    Paid { at: Time },
    Refunded { at: Time, reason: String },
}
```

## T2: Newtypes for meaning

```rust
// Bad: easy to swap, and nothing proves the email was checked.
fn invite(team: Uuid, user: Uuid, email: String) { /* ... */ }

// Good: the private field means the only way in is through the check.
pub struct Email(String);
impl FromStr for Email {
    type Err = ParseEmailError;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s.contains('@') { Ok(Self(s.to_owned())) } else { Err(ParseEmailError) }
    }
}
fn invite(team: TeamId, user: UserId, email: Email) { /* ... */ }
```

## T3: Constructive types, only where needed

```rust
// Bad: the type allows an empty list, so the code has to unwrap.
fn leader(members: &[Member]) -> &Member { members.first().unwrap() }

// Good, but only because this unwrap kept coming back: the type can't be empty.
struct Team { leader: Member, rest: Vec<Member> }
fn leader(team: &Team) -> &Member { &team.leader }
```

If nothing forces an `unwrap`, keep the `Vec`.

## T4: Parse at the boundary

```rust
// Bad: raw JSON travels inside, and every reader checks it again.
fn handle(body: serde_json::Value) -> Result<()> {
    let qty = body["qty"].as_u64().ok_or(Error::BadQty)?;
    // ...
}

// Good: serde runs the check once. Inside, `Order` is trusted.
#[derive(Deserialize)]
struct Order { sku: Sku, qty: Quantity }

#[derive(Deserialize)]
#[serde(try_from = "u32")]
struct Quantity(NonZeroU32);
impl TryFrom<u32> for Quantity {
    type Error = &'static str;
    fn try_from(n: u32) -> Result<Self, Self::Error> {
        NonZeroU32::new(n).map(Self).ok_or("qty must be at least 1")
    }
}

fn handle(order: Order) -> Result<()> { /* ... */ }
```

## E2: Typed errors

```rust
// Bad: the caller can only print it, and every call site repeats map_err.
fn load(path: &Path) -> Result<Config, String> {
    let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
    toml::from_str(&text).map_err(|e| e.to_string())
}

// Good, in a library: one variant per failure the caller can act on.
#[derive(Debug, thiserror::Error)]
pub enum LoadError {
    #[error("can't read {}", .path.display())]
    Read { path: PathBuf, #[source] source: io::Error },
    #[error("invalid config")]
    Parse(#[from] toml::de::Error),
}

// Good, in a binary: anyhow, with context at each layer.
fn load(path: &Path) -> anyhow::Result<Config> {
    let text = fs::read_to_string(path).with_context(|| format!("reading {}", path.display()))?;
    Ok(toml::from_str(&text)?)
}
```

## O2: No clone to quiet the borrow checker

```rust
// Bad: the clone exists only because `self` is borrowed during the loop.
for item in self.items.clone() { self.total += item.price; }

// Good: borrow the field, not the whole struct.
for item in &self.items { self.total += item.price; }
// Or compute first, then assign.
self.total = self.items.iter().map(|i| i.price).sum();
```

## O4: Standard traits over custom methods

```rust
// Bad: works only where you call it by name.
impl Status { fn to_string_value(&self) -> String { /* ... */ } fn parse_status(s: &str) -> Option<Self> { /* ... */ } }

// Good: now `format!`, `.parse()`, and `?` all work.
impl fmt::Display for Status { /* ... */ }
impl FromStr for Status { type Err = ParseStatusError; /* ... */ }
```

## A1: Own, don't share

```rust
// Bad: a shared counter that every task locks.
let count = Arc::new(Mutex::new(0));
for job in jobs {
    let count = Arc::clone(&count);
    tokio::spawn(async move { run(job).await; *count.lock().expect("lock poisoned") += 1; });
}

// Good: tasks hand back results, and one owner adds them up.
let mut set = JoinSet::new();
for job in jobs { set.spawn(run(job)); }
let mut count = 0;
while set.join_next().await.is_some() { count += 1; }
```

## A3: No blocking calls inside async code

```rust
// Bad: blocks a runtime thread, so other tasks stall.
async fn hash(pw: String) -> Hash { argon2::hash(&pw) }

// Good
async fn hash(pw: String) -> Result<Hash, JoinError> {
    tokio::task::spawn_blocking(move || argon2::hash(&pw)).await
}
```

## Q2: Tests run the real thing

```rust
// Bad: passes even if `save` does nothing, because it only checks the mock was called.
let mut store = MockStore::new();
store.expect_put().times(1).return_const(Ok(()));
save(&store, &doc).unwrap();

// Good: a real temp dir, then read back what a user would see.
let dir = tempfile::tempdir().unwrap();
let store = FileStore::new(dir.path());
save(&store, &doc).unwrap();
assert_eq!(store.get(doc.id).unwrap(), doc);
```

Fake only what is slow or random: the clock, the network, and randomness.

```rust
fn is_expired(token: &Token, now: SystemTime) -> bool { token.expires_at <= now }
// Test passes a fixed `now`. Production passes `SystemTime::now()`.
```
