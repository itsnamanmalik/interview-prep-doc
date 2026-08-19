---
icon: material/puzzle-outline
---

# MCP & Skills

Two open standards that solve adjacent problems and are constantly confused for each other. The distinction is worth being able to state in one sentence:

!!! tip "The one-line version"
    **MCP connects an agent to systems. Skills teach an agent a procedure.**
    MCP is an integration protocol; a Skill is packaged procedural knowledge. One
    gives the agent new *capabilities*, the other gives it new *expertise*.

Both are vendor-neutral: [MCP](https://modelcontextprotocol.io/) is a specification with SDKs in many languages, and [Agent Skills](https://agentskills.io) is a file format supported across a long list of agent products. Neither locks you to a model provider, which is why they are worth learning as engineering primitives rather than as one vendor's feature.

## Model Context Protocol (MCP)

### The problem it solves

Before MCP, every agent product wrote its own integration for every system: N agents times M systems equals N times M bespoke connectors. MCP makes that N plus M. Write one server for your ticketing system and any MCP-capable agent can use it.

### Participants

| Role | What it is |
| --- | --- |
| **MCP host** | The AI application, which coordinates one or more clients |
| **MCP client** | Maintains one dedicated connection to one server |
| **MCP server** | A program that provides context and capabilities to clients |

One client per server connection. A host talking to four servers instantiates four clients. "Local" versus "remote" server is just a description of where it runs and which transport it uses, not a different kind of thing.

### Two layers

- **Data layer** — a [JSON-RPC 2.0](https://www.jsonrpc.org/) protocol defining discovery, primitives, and notifications.
- **Transport layer** — how bytes move, plus authorisation. Two transports:
    - **stdio** — standard input/output between local processes. No network overhead, typically one client.
    - **Streamable HTTP** — HTTP POST for requests, optional Server-Sent Events for streaming. This is what remote servers use, and it supports normal HTTP auth, with OAuth recommended for obtaining tokens.

### Primitives

This is the part worth memorising. **Servers** expose three:

| Primitive | Purpose | Methods |
| --- | --- | --- |
| **Tools** | Executable functions the model can invoke | `tools/list`, `tools/call` |
| **Resources** | Data the client can read as context | `resources/list`, `resources/read` |
| **Prompts** | Reusable interaction templates | `prompts/list`, `prompts/get` |

A database server, for example, might expose a *tool* to run a query, a *resource* holding the schema, and a *prompt* with few-shot examples of good queries.

**Clients** expose one:

| Primitive | Purpose |
| --- | --- |
| **Elicitation** | Lets a server ask the user for more input or a confirmation, via `elicitation/create` |

!!! warning "Know what was deprecated"
    **Sampling** (a server asking the client's model for a completion, `sampling/createMessage`) and **logging** (server log messages delivered to the client) are **deprecated as of protocol version `2026-07-28`**. New servers should integrate with a model API directly if they need inference, and log to `stderr` on stdio or via OpenTelemetry. Interviewers who learned MCP in 2025 will often still list four client primitives, so knowing this is a cheap way to demonstrate you have read the current spec.

### Statelessness and discovery

The protocol is **stateless**: every request carries the protocol version, the sender's capabilities, and usually its identity in a `_meta` field, so a server infers nothing from previous requests. That is what makes horizontally scaled remote servers straightforward.

Servers must implement `server/discover`, which returns supported protocol versions and capabilities. Clients may call it first, but are free to send any request and handle a version error instead.

```json
{
  "jsonrpc": "2.0", "id": 1, "method": "tools/call",
  "params": {
    "name": "weather_current",
    "arguments": {"location": "San Francisco", "units": "imperial"},
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientInfo": {"name": "example-client", "version": "1.0.0"},
      "io.modelcontextprotocol/clientCapabilities": {"elicitation": {}}
    }
  }
}
```

Two operational details that follow from statelessness:

- **Caching is explicit.** List and discovery responses can carry `ttlMs` and `cacheScope`, so a client knows how long it may reuse them. Do not re-list tools on every turn.
- **Notifications are opt-in.** A client opens a long-lived `subscriptions/listen` stream naming the notification types it wants; the server then delivers matching notifications such as `notifications/tools/list_changed`. Delivery is best-effort across reconnects, so polling still matters for freshness.

The protocol also supports **extensions** on top of the core, such as a Tasks extension that returns a durable handle for a long-running request so the client can poll for the result later. That is the clean answer to "what if a tool takes ten minutes".

### Engineering concerns

- **Tool definitions cost context.** Every listed tool's name, description and JSON Schema sits in the model's context. Twenty servers with ten tools each is a real tax on both cost and accuracy. Clients that federate many servers should use **progressive tool discovery** rather than loading every tool upfront, and you should expose a curated subset per use case rather than everything you can.
- **A server is a service you operate.** Auth, deployment, versioning, rate limits, observability, on-call. "Just add an MCP server" is a deployment decision, not a config change.
- **Third-party servers are untrusted code with a trusted position.** A malicious or compromised server can return tool descriptions crafted to manipulate the model, and it sees whatever you send it. Pin versions, review what you install, and scope credentials narrowly. See [Safety & Guardrails](safety-and-guardrails.md).
- **Authorise in the server, against the caller.** Never against an argument the model chose.
- **MCP does not make a bad tool good.** Tool design still decides whether the agent succeeds; see [Agentic AI](agentic-ai.md).

## Agent Skills

### The problem it solves

An agent with the right tools still fails when it does not know *your* procedure: which checks run before a release, how your team formats a design doc, what "closing the books" means in your finance process. That knowledge usually lives in a wiki nobody reads, or gets pasted into the prompt again and again.

A **Skill** packages that procedural knowledge into a version-controlled folder the agent loads on demand.

### The format

A skill is a directory whose only required file is `SKILL.md`:

```
my-skill/
├── SKILL.md          # required: metadata + instructions
├── scripts/          # optional: executable code
├── references/       # optional: detailed documentation
├── assets/           # optional: templates, schemas, images
└── ...
```

`SKILL.md` is YAML frontmatter plus Markdown instructions. The standard defines these fields:

| Field | Required | Constraints |
| --- | --- | --- |
| `name` | Yes | 1 to 64 chars, lowercase `a-z`, `0-9` and hyphens; no leading, trailing or consecutive hyphens; must match the parent directory name |
| `description` | Yes | 1 to 1024 chars. What it does **and when to use it** |
| `license` | No | Licence name, or the name of a bundled licence file |
| `compatibility` | No | Up to 500 chars. Environment requirements: packages, network access, intended product |
| `metadata` | No | Arbitrary string key/value map for client-specific properties |
| `allowed-tools` | No | Space-separated pre-approved tools. Experimental; support varies |

```markdown
---
name: release-checklist
description: Runs our pre-release verification: changelog, migrations, feature
  flags and rollback plan. Use when preparing or cutting a release, or when the
  user mentions shipping, deploying to production, or a release branch.
compatibility: Requires git and access to the CI API
---

## Steps

1. Confirm every merged PR since the last tag has a changelog entry.
2. Run `scripts/check_migrations.py` and stop if any migration is not reversible.
3. ...

See [references/ROLLBACK.md](references/ROLLBACK.md) for the rollback procedure.
```

Individual agent products extend the format with their own frontmatter fields, which is allowed but not portable. Keep anything you want to reuse across tools within the standard fields above.

### Progressive disclosure

This is the mechanism that makes Skills cheap, and the thing to explain if asked how they differ from stuffing instructions into a system prompt.

| Stage | What loads | Budget |
| --- | --- | --- |
| **1. Discovery** | `name` + `description` of every available skill, at startup | ~100 tokens each |
| **2. Activation** | The full `SKILL.md` body, once the agent decides the skill is relevant | Under ~5,000 tokens recommended |
| **3. Execution** | Files under `references/`, `scripts/`, `assets/`, read only when needed | Unbounded, paid only on use |

Consequences worth stating out loud:

- **The `description` is the routing key.** It is the only thing in context at selection time, so it must name the trigger conditions and the vocabulary users actually use. A vague description means the skill never activates, which looks exactly like the skill not working.
- **You can keep dozens of skills on hand** for the price of their descriptions. That is the whole point.
- **Keep `SKILL.md` under about 500 lines** and push depth into `references/`, one level deep. Deep reference chains make the agent read three files to learn one thing.
- **Once activated, the body stays in context**, so every line is a recurring cost across turns. Write instructions, not essays.

### Engineering concerns

- **Skills are code review surface.** They are Markdown in a repo, so review them in PRs like anything else: they change agent behaviour and can contain instructions you would not approve.
- **A skill from an untrusted source is a prompt-injection payload** with an invitation to load it. Treat community skills like third-party dependencies.
- **Bundled scripts need a sandbox.** If the agent executes `scripts/*.py`, that runs on whatever machine hosts the agent. No ambient credentials, no network unless required.
- **Validate them in CI.** The reference library `skills-ref validate ./my-skill` checks frontmatter and naming, which catches the typo that silently disables a skill.
- **Version them with the thing they describe.** A release checklist in the same repo as the release scripts stays true; one in a wiki does not.

## The comparison

| | **MCP** | **Skills** |
| --- | --- | --- |
| **Answers** | What can the agent *do*? | *How* should the agent do it? |
| **Supplies** | Capabilities and live data | Procedural knowledge and context |
| **Artefact** | A running server process | A folder of files in a repo |
| **Wire format** | JSON-RPC 2.0 over stdio or Streamable HTTP | None; the host reads files |
| **Runtime cost** | A service to deploy, auth and monitor | Zero; it is text on disk |
| **Context cost** | Tool schemas held per session, mitigated by progressive tool discovery | ~100 tokens per skill until activated |
| **Loading** | Listed up front, called on demand | Description up front, body on activation, resources on use |
| **Who triggers it** | The model calls a tool | The model matches the description, or a user invokes it directly |
| **State and freshness** | Live: reads your systems at call time | Static: whatever the file says at load time |
| **Auth** | OAuth or HTTP auth per server, enforced server-side | Inherits the agent's permissions; no auth of its own |
| **Failure mode** | Server down, rate limited, schema mismatch, tool sprawl | Never activates (weak description), or is stale and confidently wrong |
| **Change control** | Deploy a new server version | Merge a PR |
| **Good at** | Reaching systems the agent cannot otherwise touch | Making the agent do a known task consistently |
| **Bad at** | Encoding a workflow (a tool call is one step, not a procedure) | Anything needing live data or credentials |

### What about MCP `prompts` versus Skills?

The sharpest version of the question, because they genuinely overlap: both ship reusable instructions.

- **MCP `prompts`** are templates *served by the system that owns the domain*, fetched over the protocol, and versioned with that server. Good for "here is how to query me well", shipped by the team that runs the database.
- **Skills** live with *your* team, in *your* repo, describe *your* workflow, can bundle scripts and reference material, and load progressively.

If the instructions belong to the integrated system, `prompts` is the natural home. If they encode your organisation's process, that is a Skill. In practice Skills see far wider use, because most procedural knowledge is local to a team rather than to a vendor's API.

## Choosing, and composing

**Reach for MCP when** the agent needs to read or act on a system it cannot otherwise reach; the data must be live; access needs its own authentication and audit trail; or several different agent products need the same integration.

**Reach for a Skill when** the agent already has the tools but uses them inconsistently; you keep pasting the same instructions; the task is a multi-step procedure with an order that matters; the knowledge is yours rather than a vendor's; or you want the same behaviour across several agent tools.

**They compose, and that is the intended end state.** MCP supplies the verbs; the Skill supplies the sentence.

```
Skill: incident-triage
  description: Triage a production incident. Use when an alert fires or the
    user reports an outage.
  body:
    1. Query the metrics MCP server for error rate by service, last 30 min.
    2. Pull recent deploys from the deploy MCP server; correlate by timestamp.
    3. Search the ticket MCP server for open incidents on the same service.
    4. Write the summary using assets/incident-template.md.
    5. Never roll back without explicit approval; see references/ROLLBACK.md.
```

Nothing in that skill is a capability. Every capability comes from an MCP server. What the skill adds is the order, the correlation step, the template, and the one hard rule about rollbacks. Without it, the agent has all the same tools and improvises differently every time.

The corollary is a genuinely useful design rule: **when an agent misbehaves, ask whether it lacked a capability or lacked a procedure.** Missing capability means a tool or server. Inconsistent behaviour with the right tools available means a skill. Reaching for the wrong one is the most common wasted week in this area.

## Anti-patterns

| Anti-pattern | Why it hurts |
| --- | --- |
| **Connecting every MCP server you can find** | Tool sprawl degrades selection accuracy and inflates every request's context |
| **One mega-skill for everything** | Its description cannot be specific, so it activates at the wrong times or never |
| **A skill that duplicates a tool** | Procedure and capability confused; the tool already does it |
| **A skill with a vague description** | Silently never loads; indistinguishable from broken |
| **Encoding secrets in a skill** | It is a file in a repo, read by a model, often echoed into logs |
| **An MCP server wrapping your whole database with `execute_sql`** | Maximum blast radius, exactly what least-privilege tool design exists to prevent |
| **Treating a third-party skill or server as trusted** | Both are execution and injection surface; review them as dependencies |
| **Instructions in a skill that must be enforced** | A model may ignore prose. Approval gates and limits belong in code, not in Markdown |

## What to say in an interview

> They solve different problems and I use both. MCP is an integration protocol: JSON-RPC over stdio or Streamable HTTP, servers exposing tools, resources and prompts, clients exposing elicitation, stateless with per-request capability metadata so remote servers scale. It turns N agents times M systems into N plus M. Skills are an open file format for procedural knowledge: a folder with a `SKILL.md`, loaded by progressive disclosure so only the name and description sit in context until the task matches, then the body, then bundled references and scripts on demand. So MCP gives the agent capabilities and a Skill teaches it our procedure for using them. My working rule when an agent misbehaves is to ask whether it lacked a capability or a procedure, because the fix is a server in the first case and a skill in the second. And I treat both as supply chain: a third-party server can craft tool descriptions to manipulate the model, and a third-party skill is a prompt-injection payload you have invited in, so both get reviewed, pinned and given least privilege.
