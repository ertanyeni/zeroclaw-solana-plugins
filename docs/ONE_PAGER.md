# Zero-custody Solana tools for ZeroClaw

## Thesis

A ZeroClaw agent can safely help move money on Solana **without ever holding a
key**. The agent proposes; the human or a Squads multisig disposes. This keeps
useful financial workflows inside the agent while leaving authorization at the
wallet boundary, where the payer can inspect and approve the exact transaction.

## The toolbox

Each plugin is a standalone, single-tool `wasm32-wasip2` component implementing
ZeroClaw's WIT `tool-plugin` world.

| Tool | Tier | Job | Authority |
|---|---|---|---|
| `sns_resolve` | T0 | Resolve a `.sol` name to its current on-chain owner | Read-only Solana RPC |
| `token_risk_check` | T0 | Assess mint/freeze authority, token program, and holder concentration | Read-only Solana RPC |
| `solana_pay_request` | T1 | Build a validated Solana Pay URL for SOL or SPL tokens | No network, signer, or key |
| `unsigned_transfer` | T1 | Assemble an unsigned SOL/SPL transfer for a human or Squads to sign | Read-only RPC; never signs |

Together they form a safe payment path: `sns_resolve` turns a human-readable
recipient into a wallet address; `token_risk_check` vets an SPL mint before it is
used; `solana_pay_request` produces a Solana Pay request a human scans and signs;
and `unsigned_transfer` assembles a real, ready-to-sign transaction whose signature
still stays with the owner. The agent can research, validate, and propose — build
the transaction itself, even — but cannot move funds by itself.

## Deny by default

Capabilities are minimal per tool. `solana-pay-request` declares
`permissions = []`. The two T0 readers receive only HTTP client and config-read
permissions for RPC access. No component imports signing or secret-management
capabilities, and every `execute` path records an event through the host logging
interface.

The tools fail closed at each trust boundary:

- Payment requests reject malformed recipients, mints, references, and amounts;
  free-form display fields are percent-encoded, while the validated recipient is
  preserved verbatim for wallet review.
- Token checks never turn missing, malformed, or unknown mint data into a green
  verdict. Unverifiable assets are high risk.
- Name resolution derives the account deterministically and rejects absent,
  malformed, ownerless, and unsupported subdomain results.

Prompt-injection transcripts and offline adversarial tests in every plugin make
these guarantees reviewable. Release builds expose exactly the ZeroClaw `tool`
and `plugin-info` interfaces; networked components use host-provided `wasi:http`.

## Why it fits the bounty

- **Utility:** a coherent workflow for identity, asset due diligence, and real
  Solana Pay requests rather than three disconnected demos.
- **Safety:** zero custody, least privilege, human/multisig approval, deterministic
  validation, and explicit fails-closed behavior.
- **Code quality:** small auditable cores, thin WIT shims, offline tests, golden
  vectors, clean rustfmt/clippy, and verified WASI component exports.
- **Mergeability:** each plugin follows the upstream `redact-text` layout and is
  independently buildable, reviewable, and installable.
- **Demo value:** resolve a `.sol` name, vet the requested token, render a Solana
  Pay QR, and complete the final approval in a wallet without exposing a key.

## Roadmap

Next, `lending-health` (T0) would monitor collateral and liquidation distance using
read-only protocol data; `unsigned_transfer` would grow Token-2022 support and a
Squads-proposal output; and a `simulateTransaction` preview would let the human see
the expected effect before signing. All preserve the same rule: the agent may
understand, propose, and even build financial actions, but authority stays with the
owner.
