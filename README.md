# zeroclaw-solana-plugins

A toolbox of **zero-custody Solana tool plugins** for the
[ZeroClaw](https://github.com/zeroclaw-labs/zeroclaw) agent runtime, built for the
Superteam Earn bounty *"Build Solana-native plugins for Zeroclaw"* (5000 USDG).

Each plugin is a self-contained `wasm32-wasip2` WIT component implementing the
`tool-plugin` world from `wit/v0`, matching the upstream reference plugin
`redact-text`. This repo is the **development harness** (it vendors `wit/v0` so the
plugins build against `../../wit/v0`); the plugins are submitted upstream as a PR
to [`zeroclaw-labs/zeroclaw-plugins`](https://github.com/zeroclaw-labs/zeroclaw-plugins).

## Thesis

The bounty asks: *how should an autonomous agent handle money?* Our answer is
**zero custody** — the agent **proposes**, a human (or a Squads multisig)
**disposes**. No plugin here holds a private key. The safety blast radius is zero,
yet money still moves on-chain in a live demo.

## Plugins

| plugin | tier | what it does | keys? | network? | status |
|---|---|---|---|---|---|
| **solana-pay-request** | T1 | build a Solana Pay URL/QR for a SOL/SPL payment a human signs | none | none | ✓ built + verified |
| **token-risk-check** | T0 | mint/freeze authority + holder concentration → red/amber/green | none | RPC (read) | ✓ built + verified |
| **sns-resolve** | T0 | resolve a `.sol` name to its owner address | none | RPC (read) | ✓ built + verified |

Each: `cargo test` green, builds to `wasm32-wasip2`, `wasm-tools component wit`
shows exactly the `tool` + `plugin-info` exports. The tools chain — `sns-resolve`
turns *"pay bonfida.sol"* into an address that `solana-pay-request` invoices and
`token-risk-check` vets — over a shared, hardened `rpc.rs` core.

**Roadmap (stretch):** `unsigned-transfer` (T1: assemble an unsigned SOL/SPL tx
for a human/Squads to sign) · `lending-health` (T0: liquidation-distance monitor).

## Layout

```
wit/v0/                 # ZeroClaw plugin WIT contract (vendored for local builds)
plugins/<name>/         # one wit-bindgen component per directory
  src/lib.rs            # thin #[cfg(target_family = "wasm")] shim; logs via log-record
  src/<core>.rs         # pure logic, host-testable with `cargo test`
  tests/                # golden-vector + fails-closed tests
  manifest.toml         # capabilities + minimal permissions
  README.md             # custody tier, threat model, prompt-injection transcript
```

## Build a plugin

```bash
cd plugins/solana-pay-request
cargo test
rustup target add wasm32-wasip2
cargo build --release --target wasm32-wasip2
wasm-tools component wit target/wasm32-wasip2/release/*.wasm
```

## License

MIT OR Apache-2.0
