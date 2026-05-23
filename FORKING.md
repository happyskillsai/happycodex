# HappyCodex Fork Notes

## Table of Contents

### 1. Fork Purpose
#### 1.1 Why This Fork Exists
#### 1.2 What This Fork Changes
#### 1.3 What This Fork Does Not Change Yet

### 2. Repository Setup
#### 2.1 Remotes
#### 2.2 Local Branches
#### 2.3 Current Downstream Commit
#### 2.4 Upstream Sync Strategy

### 3. Feature Overview
#### 3.1 User-Facing Behavior
#### 3.2 Skill Invocation Model
#### 3.3 Argument Hint Model
#### 3.4 Side Conversation and Running Task Rules

### 4. Technical Architecture
#### 4.1 Skill Metadata Loading
#### 4.2 Protocol and App Server Propagation
#### 4.3 TUI Slash Command Discovery
#### 4.4 Composer Dispatch
#### 4.5 ChatWidget Submission
#### 4.6 Existing Skill Mention Reuse
#### 4.7 Queue Handling

### 5. End-to-End Flows
#### 5.1 Selecting a Skill From the Slash Popup
#### 5.2 Typing a Bare Skill Slash Command
#### 5.3 Typing a Skill Slash Command With Arguments
#### 5.4 Queueing a Skill Command While a Task Is Running
#### 5.5 Loading Skills Through App Server

### 6. Changed File Structure
#### 6.1 Core Skill Model and Loader
#### 6.2 Protocol and App Server Boundary
#### 6.3 TUI Slash Command Surface
#### 6.4 TUI ChatWidget Submission Surface
#### 6.5 Tests and Fixtures

### 7. Changed Files in Detail
#### 7.1 codex-rs/core-skills/src/model.rs
#### 7.2 codex-rs/core-skills/src/loader.rs
#### 7.3 codex-rs/core-skills/src/loader_tests.rs
#### 7.4 codex-rs/protocol/src/protocol.rs
#### 7.5 codex-rs/app-server-protocol/src/protocol/v2/plugin.rs
#### 7.6 codex-rs/app-server/src/request_processors/catalog_processor.rs
#### 7.7 codex-rs/app-server/src/request_processors/plugins.rs
#### 7.8 codex-rs/tui/src/bottom_pane/slash_commands.rs
#### 7.9 codex-rs/tui/src/bottom_pane/command_popup.rs
#### 7.10 codex-rs/tui/src/bottom_pane/chat_composer.rs
#### 7.11 codex-rs/tui/src/chatwidget/input_flow.rs
#### 7.12 codex-rs/tui/src/chatwidget/slash_dispatch.rs
#### 7.13 codex-rs/tui/src/chatwidget/user_messages.rs
#### 7.14 codex-rs/tui/src/chatwidget/input_submission.rs
#### 7.15 codex-rs/tui/src/chatwidget/skills.rs
#### 7.16 Test-Only Struct Initializer Updates

### 8. Data Model Additions
#### 8.1 SkillMetadata.argument_hint
#### 8.2 SkillSlashCommand
#### 8.3 SlashCommandItem.Skill
#### 8.4 CommandItem.Skill
#### 8.5 InputResult.SkillCommand
#### 8.6 UserMessage.has_content

### 9. Compatibility and Merge Notes
#### 9.1 Upstream Conflict Hotspots
#### 9.2 Why the Patch Reuses Existing Skill Mentions
#### 9.3 Known Limitations
#### 9.4 Future Work

### 10. Validation Notes
#### 10.1 Tests Added
#### 10.2 Tests Updated
#### 10.3 Tests Not Run During Fork Setup

## 1. Fork Purpose

### 1.1 Why This Fork Exists

HappyCodex is a downstream fork of OpenAI Codex. The purpose of the fork is to distribute a Codex-compatible CLI with HappySkills-specific skill invocation ergonomics while keeping the codebase close enough to upstream that future OpenAI Codex releases can be merged regularly.

The fork exists because the desired feature is unlikely to be accepted upstream through a public pull request path. The goal is therefore to carry a small, understandable downstream patch until upstream Codex supports equivalent behavior or the fork is no longer needed.

### 1.2 What This Fork Changes

The current downstream patch adds first-class slash-command invocation for loaded skills in the TUI.

Before this patch, skills could be mentioned with `$skill-name`, and the skill-loading system could expose skill metadata to the model. After this patch, every loaded skill can also appear as a slash command:

```text
/skill-name
/skill-name optional arguments here
```

Submitting a skill slash command creates a user message that contains:

- the command arguments as the normal user text,
- a structured skill mention binding pointing at the selected skill path,
- any existing image attachments, text elements, remote image URLs, or mention bindings that belong to the submission.

The existing skill mention conversion pipeline then turns the binding into a `UserInput::Skill`, so the model receives the same explicit skill invocation shape used by normal `$skill` mentions.

### 1.3 What This Fork Does Not Change Yet

This commit does not rename the npm package from Codex to HappyCodex yet.

It does not modify:

- `codex-cli/package.json`,
- `codex-cli/bin/codex.js`,
- npm optional dependency names,
- release workflows,
- installer scripts,
- GitHub Actions for upstream sync,
- README branding.

Those are the next packaging and distribution steps. This document only describes the committed feature patch plus the current fork operating model.

## 2. Repository Setup

### 2.1 Remotes

The local repository was converted from a plain clone of OpenAI Codex into a downstream fork setup.

Current remotes:

```text
origin   https://github.com/happyskillsai/happycodex.git
upstream https://github.com/openai/codex.git
```

The `upstream` push URL is intentionally disabled:

```text
upstream DISABLED
```

This prevents accidental pushes to OpenAI's repository.

### 2.2 Local Branches

The local downstream branch is:

```text
happycodex/main
```

It tracks:

```text
origin/main
```

The original OpenAI branch is still available locally as:

```text
main
```

It tracks:

```text
upstream/main
```

### 2.3 Current Downstream Commit

The first downstream feature commit is:

```text
0ecb482a08 Add HappySkills skill invocation support
```

Patch size:

```text
23 files changed, 558 insertions, 84 deletions
```

### 2.4 Upstream Sync Strategy

The intended long-term branch discipline is:

1. Keep `upstream/main` or upstream release tags as the source of truth.
2. Keep HappyCodex-specific changes as a small patch set on top.
3. For every upstream release, merge or rebase upstream into a sync branch.
4. Run checks.
5. Open a sync PR in `happyskillsai/happycodex`.
6. Publish only after the sync PR passes and is merged.

Do not auto-publish directly after an automatic upstream merge. Codex changes can affect protocol types, TUI submission logic, app-server request processors, and release packaging. A sync PR gives the fork a review and CI gate.

## 3. Feature Overview

### 3.1 User-Facing Behavior

Loaded skills are exposed as slash commands in the command popup.

Example:

```text
/happyskills-design
/happyskills-design audit this skill
```

The popup can show a skill's argument hint before the description:

```text
/review-pr    [pr-number]  Review a pull request
```

Skill commands participate in prefix matching, so typing `/rev` can find `/review-pr`.

### 3.2 Skill Invocation Model

Skill slash commands do not introduce a new backend invocation primitive. They intentionally reuse the existing explicit skill mention path.

The slash command:

```text
/my-skill do the thing
```

is converted into a user message with:

```text
text = "do the thing"
mention_bindings += MentionBinding {
    mention: "my-skill",
    path: "skill:///absolute/path/to/my-skill/SKILL.md"
}
```

The existing submission code strips the `skill://` prefix, resolves the path against loaded skills, and emits:

```rust
UserInput::Skill {
    name: "my-skill",
    path: "/absolute/path/to/my-skill/SKILL.md",
}
```

### 3.3 Argument Hint Model

The fork adds `argument_hint` to skill metadata.

The loader supports two frontmatter sources:

```yaml
argument-hint: "[scope] [summary]"
```

or:

```yaml
arguments:
  - pr-number
  - focus
```

The explicit `argument-hint` wins. If it is absent, `arguments` is converted into bracketed placeholders:

```text
[pr-number] [focus]
```

Numeric-only or empty argument names are ignored.

### 3.4 Side Conversation and Running Task Rules

Skill slash commands are disabled in side conversations.

Reason: they submit a user turn that loads a skill into the active conversation. Side conversations have narrower command availability rules, and this patch follows the same conservative treatment as service-tier commands.

Skill slash commands are disabled while a task is in progress for immediate dispatch.

Reason: direct skill invocation starts a new user turn. If a task is already running, it should not interleave a second active turn. Queued command handling still exists for submissions that are queued by the composer.

## 4. Technical Architecture

### 4.1 Skill Metadata Loading

`codex-rs/core-skills/src/loader.rs` now parses:

- `argument-hint`,
- `arguments` as either a string or a list.

The parsed value is stored on `SkillMetadata.argument_hint`.

The field is sanitized with the same single-line normalization style used by other skill metadata and validated against the same 1024-character maximum as descriptions.

### 4.2 Protocol and App Server Propagation

`argument_hint` is added to the protocol skill metadata structs so the value survives the trip from core skill loading to TUI surfaces:

```text
core-skills SkillMetadata
  -> app-server protocol SkillMetadata
  -> app-server protocol SkillSummary
  -> TUI ProtocolSkillMetadata
  -> TUI core SkillMetadata clone
  -> SkillSlashCommand
```

Remote plugin catalog skills do not currently carry argument hints, so they set `argument_hint: None`.

### 4.3 TUI Slash Command Discovery

`codex-rs/tui/src/bottom_pane/slash_commands.rs` now models skills as slash command items.

The central enum changed from:

```rust
enum SlashCommandItem {
    Builtin(SlashCommand),
    ServiceTier(ServiceTierCommand),
}
```

to:

```rust
enum SlashCommandItem {
    Builtin(SlashCommand),
    ServiceTier(ServiceTierCommand),
    Skill(SkillSlashCommand),
}
```

This keeps built-in commands, service-tier commands, and skill commands under one lookup API:

- `commands_for_input`,
- `find_slash_command`,
- `has_slash_command_prefix`.

### 4.4 Composer Dispatch

`ChatComposer` now returns `InputResult::SkillCommand` when the user selects or submits a skill slash command.

The result carries:

- the selected skill command,
- the argument string,
- rebased `TextElement` ranges for inline arguments.

Bare commands use empty args:

```rust
InputResult::SkillCommand(command, String::new(), Vec::new())
```

Commands with args use the trimmed rest of the slash input:

```rust
InputResult::SkillCommand(command, trimmed_rest.to_string(), args_elements)
```

### 4.5 ChatWidget Submission

`ChatWidget` handles `InputResult::SkillCommand` in `input_flow.rs` and delegates to `slash_dispatch.rs`.

The dispatch code:

1. rejects side conversation use,
2. rejects immediate invocation while a task is running,
3. prepares inline args when needed,
4. captures local images, remote images, and mention bindings,
5. appends a skill mention binding,
6. submits or queues the resulting user message.

### 4.6 Existing Skill Mention Reuse

The most important design decision is that skill slash commands reuse the existing skill mention pipeline.

This avoids adding a separate skill invocation protocol path. The new slash command path only needs to synthesize:

```rust
MentionBinding {
    mention: command.name,
    path: format!("skill://{}", command.path.display()),
}
```

Then existing submission code produces the final `UserInput::Skill`.

### 4.7 Queue Handling

Queued slash prompt draining now knows about skills.

When a queued prompt is parsed as a slash command, `submit_queued_slash_prompt` builds the current `SkillSlashCommand` list from loaded skills and passes it to `find_slash_command`.

For skill commands:

- no args: submit an empty-text skill invocation,
- with args: trim and rebase argument text elements, then submit the skill invocation with the argument text.

Service-tier commands with inline args still fall back to normal text submission because service-tier commands do not support inline args.

## 5. End-to-End Flows

### 5.1 Selecting a Skill From the Slash Popup

1. User types `/`.
2. `ChatComposer::sync_command_popup` creates a `CommandPopup`.
3. The popup receives:
   - built-in commands,
   - service-tier commands,
   - `skill_slash_commands()`.
4. The user highlights a skill command.
5. Pressing Enter returns `InputResult::SkillCommand`.
6. `ChatWidget::handle_composer_input_result` dispatches it.
7. `ChatWidget::submit_skill_command_user_message` appends a `skill://` mention binding.
8. Normal submission emits `UserInput::Skill`.

### 5.2 Typing a Bare Skill Slash Command

Input:

```text
/my-skill
```

Flow:

1. `try_dispatch_bare_slash_command` parses `my-skill`.
2. `find_slash_command` resolves it as `SlashCommandItem::Skill`.
3. The composer clears the draft.
4. `InputResult::SkillCommand(command, "", [])` is returned.
5. ChatWidget submits a user message with empty text and a skill binding.
6. `UserMessage.has_content()` treats mention bindings as content, so the empty-text skill invocation is not dropped.

### 5.3 Typing a Skill Slash Command With Arguments

Input:

```text
/my-skill inspect src/main.rs
```

Flow:

1. `try_dispatch_slash_command_with_args` parses:
   - name: `my-skill`,
   - rest: `inspect src/main.rs`.
2. `find_slash_command` resolves the skill.
3. `SlashCommandItem::Skill` reports `supports_inline_args() == true`.
4. Text elements are rebased from whole-input coordinates into argument-string coordinates.
5. The composer returns `InputResult::SkillCommand(command, "inspect src/main.rs", args_elements)`.
6. ChatWidget submits the args as the visible user text and the skill as a structured skill input.

### 5.4 Queueing a Skill Command While a Task Is Running

If a slash command is queued for later parsing, `QueuedInputAction::ParseSlash` causes `submit_queued_slash_prompt` to re-parse it at dequeue time.

For a skill command:

1. current skills are read from `bottom_pane.skills()`,
2. each skill becomes a `SkillSlashCommand`,
3. the queued slash name resolves through `find_slash_command`,
4. the user message is submitted with the selected skill binding.

This matters because loaded skills can be refreshed between the time input is queued and the time it is drained.

### 5.5 Loading Skills Through App Server

App-server skill list responses now include `argument_hint`.

The TUI conversion function `protocol_skill_to_core` copies that value into its local `SkillMetadata`. This is required because the slash command popup is constructed from the TUI's local skill list, not directly from the loader.

## 6. Changed File Structure

### 6.1 Core Skill Model and Loader

```text
codex-rs/core-skills/src/
  model.rs
  loader.rs
  loader_tests.rs
  injection_tests.rs
  invocation_utils_tests.rs
  manager_tests.rs
  render.rs
```

Purpose:

- add `argument_hint` to loaded skill metadata,
- parse it from `SKILL.md` frontmatter,
- update all affected tests and constructors.

### 6.2 Protocol and App Server Boundary

```text
codex-rs/protocol/src/
  protocol.rs

codex-rs/app-server-protocol/src/protocol/v2/
  plugin.rs

codex-rs/app-server/src/request_processors/
  catalog_processor.rs
  plugins.rs

codex-rs/tui/src/chatwidget/
  skills.rs
```

Purpose:

- carry `argument_hint` from core to app-server clients and back into TUI state.

### 6.3 TUI Slash Command Surface

```text
codex-rs/tui/src/bottom_pane/
  slash_commands.rs
  command_popup.rs
  chat_composer.rs
  mod.rs
```

Purpose:

- represent skill slash commands,
- display skills in slash popup,
- parse skill slash commands,
- return skill-specific input results.

### 6.4 TUI ChatWidget Submission Surface

```text
codex-rs/tui/src/chatwidget/
  input_flow.rs
  slash_dispatch.rs
  input_submission.rs
  user_messages.rs
```

Purpose:

- handle `InputResult::SkillCommand`,
- convert skill slash invocation into a user message with a structured skill binding,
- prevent empty-text skill invocations from being discarded.

### 6.5 Tests and Fixtures

```text
codex-rs/core/src/session/tests.rs
codex-rs/tui/src/chatwidget/tests/composer_submission.rs
codex-rs/tui/src/chatwidget/tests/helpers.rs
```

Purpose:

- update test struct construction for `argument_hint`,
- keep existing behavior tests compiling against the expanded metadata structs.

## 7. Changed Files in Detail

### 7.1 codex-rs/core-skills/src/model.rs

Change:

- Added `pub argument_hint: Option<String>` to `SkillMetadata`.

Reason:

- Slash command popup descriptions need a user-facing argument usage hint per skill.
- The field has to live in core metadata because the loader is the authoritative source for `SKILL.md` frontmatter.

Behavioral impact:

- All `SkillMetadata` constructors must now set `argument_hint`.
- `None` preserves existing behavior for skills that do not define hints.

### 7.2 codex-rs/core-skills/src/loader.rs

Change:

- Extended `SkillFrontmatter` with:
  - `argument_hint: Option<String>` mapped from YAML key `argument-hint`,
  - `arguments: Option<SkillArgumentsFrontmatter>`.
- Added `SkillArgumentsFrontmatter` as an untagged enum supporting:
  - a single string,
  - a list of strings.
- Added `MAX_ARGUMENT_HINT_LEN`.
- Added `argument_names_hint`.
- Added `valid_argument_name`.
- Populated `SkillMetadata.argument_hint`.
- Validated `argument-hint` length.

Reason:

- HappySkills skill frontmatter commonly documents invocation arguments.
- Codex needs a normalized field that the TUI can display beside slash commands.

Exact parsing behavior:

- `argument-hint` is sanitized as a single line.
- Empty `argument-hint` is ignored.
- If `argument-hint` is absent, `arguments` is converted into bracketed placeholders.
- String `arguments` is split on whitespace.
- List `arguments` is read item by item.
- Empty items are ignored.
- Numeric-only names are ignored.

Example:

```yaml
arguments:
  - pr-number
  - focus
```

becomes:

```text
[pr-number] [focus]
```

### 7.3 codex-rs/core-skills/src/loader_tests.rs

Change:

- Added `argument_hint: None` to existing expected `SkillMetadata` values.
- Added `parses_skill_argument_hint_frontmatter`.
- Added `derives_skill_argument_hint_from_arguments_frontmatter`.

Reason:

- Existing loader tests need to assert the expanded struct shape.
- New tests protect both explicit and derived hint parsing.

Coverage added:

- Direct `argument-hint` frontmatter is loaded.
- `arguments` list frontmatter is transformed into bracketed argument hint text.

### 7.4 codex-rs/protocol/src/protocol.rs

Change:

- Added optional `argument_hint` to protocol-level `SkillMetadata`.

Reason:

- Protocol clients need access to the field.
- The TUI receives skills through protocol-shaped metadata in some paths.

Compatibility:

- The field is optional and skipped during serialization when `None`.

### 7.5 codex-rs/app-server-protocol/src/protocol/v2/plugin.rs

Change:

- Added optional `argument_hint` to v2 `SkillMetadata`.
- Added optional `argument_hint` to v2 `SkillSummary`.
- Copied `CoreSkillMetadata.argument_hint` in `impl From<CoreSkillMetadata> for SkillMetadata`.

Reason:

- App-server catalog and plugin APIs expose skill summaries and metadata.
- The TUI and other app-server clients need the field without re-reading skill files.

Compatibility:

- The field is optional and omitted when absent.

### 7.6 codex-rs/app-server/src/request_processors/catalog_processor.rs

Change:

- Copied `skill.argument_hint.clone()` into app-server `SkillMetadata`.

Reason:

- Catalog skill list responses must preserve the hint from core skill loading.

### 7.7 codex-rs/app-server/src/request_processors/plugins.rs

Change:

- Copied `skill.argument_hint.clone()` into local plugin skill summaries.
- Set `argument_hint: None` for remote plugin catalog skill summaries.

Reason:

- Local plugin skills can carry loader metadata.
- Remote catalog skill payloads do not currently expose this field, so they remain compatible with `None`.

### 7.8 codex-rs/tui/src/bottom_pane/slash_commands.rs

Change:

- Imported `SkillMetadata`.
- Added `SkillSlashCommand`.
- Added `SkillSlashCommand::from_skill`.
- Added `SlashCommandItem::Skill`.
- Updated `SlashCommandItem` methods:
  - `command`,
  - `supports_inline_args`,
  - `available_in_side_conversation`,
  - `available_during_task`.
- Updated `commands_for_input` to accept and append skill commands.
- Updated `find_slash_command` to resolve skill names after built-ins and service-tier commands.
- Updated `has_slash_command_prefix` to include skills.
- Added tests for skill command resolution and prefix matching.

Reason:

- Skills must participate in the same slash command lookup and popup filtering system as existing slash commands.

Important ordering:

1. Built-ins are resolved first.
2. Service-tier commands are resolved second when enabled.
3. Skill commands are resolved last.

This means a skill whose name collides with a built-in command will not override the built-in command.

### 7.9 codex-rs/tui/src/bottom_pane/command_popup.rs

Change:

- Added `CommandItem::Skill`.
- `CommandPopup::new` now accepts `skill_commands`.
- Popup command generation now includes skills.
- Filtering works over skill command names.
- `CommandItem::command` supports skills.
- `CommandItem::description` supports skills.
- Added `popup_description`.
- Skill popup descriptions render `argument_hint` before description when present.
- Updated tests to pass the new constructor argument.
- Added `skill_command_displays_argument_hint_in_description`.

Reason:

- The slash popup is the primary discovery UI for slash commands.
- Skills need the same completion and discovery behavior as built-ins.
- Argument hints should be visible without requiring the user to open the skill file.

Display behavior:

```text
[hint]  description
```

If the description is empty, only the hint is shown.

### 7.10 codex-rs/tui/src/bottom_pane/chat_composer.rs

Change:

- Imported `SkillSlashCommand`.
- Added `InputResult::SkillCommand(SkillSlashCommand, String, Vec<TextElement>)`.
- Enter on selected popup skill returns `SkillCommand`.
- Bare slash command dispatch can return `SkillCommand`.
- Slash command with args can return `SkillCommand`.
- Slash command validation now considers skills.
- Slash command elementization now considers skills.
- Slash prefix detection now considers skills.
- Added `skill_slash_commands()` helper.
- `CommandPopup::new` receives the current skill slash command list.
- Vim-mode reset treats `SkillCommand` as a successful dispatch.
- Existing tests were updated to include a panic arm for unexpected `SkillCommand`.

Reason:

- The composer owns input parsing and popup completion.
- It must be able to distinguish a selected skill command from a normal text submission.

Specific behavior:

- `/skill` with no args returns `SkillCommand(command, "", [])`.
- `/skill args` returns `SkillCommand(command, "args", rebased_elements)`.
- Unknown slash command validation now recognizes skill names.
- Skill slash commands can be elementized like known slash commands when followed by a space.

### 7.11 codex-rs/tui/src/chatwidget/input_flow.rs

Change:

- Replaced an empty-message check with `user_message.has_content()`.
- Added handling for `InputResult::SkillCommand`.

Reason:

- A bare skill command may have empty text but still has semantic content through a mention binding.
- The input flow must dispatch skill commands instead of treating them as normal submissions.

### 7.12 codex-rs/tui/src/chatwidget/slash_dispatch.rs

Change:

- Imported `SkillSlashCommand`.
- Added `handle_skill_command_dispatch`.
- Added `submit_skill_command_user_message`.
- Updated queued slash prompt parsing to include current skill commands.
- Updated queued slash command execution to handle skill commands.
- Adjusted inline-args command handling so non-built-in inline-capable commands can be skills.

Reason:

- ChatWidget owns app-level effects for slash commands.
- The composer only parses; ChatWidget must turn the parsed skill command into a user message and submit or queue it correctly.

Dispatch behavior:

- Side conversation: reject and show an error.
- Running task: reject immediate dispatch and show an error.
- Empty args: submit an empty text message plus a skill binding.
- Non-empty args: prepare/rebase inline args and submit them as text.
- Attachments and existing mention bindings are preserved.

Generated binding:

```rust
MentionBinding {
    mention: command.name,
    path: format!("skill://{}", command.path.display()),
}
```

The `skill://` prefix makes the synthetic slash-command binding unambiguous while still allowing existing code to strip it before path comparison.

### 7.13 codex-rs/tui/src/chatwidget/user_messages.rs

Change:

- Added `UserMessage::has_content`.

Reason:

- Previous empty-message checks only considered:
  - text,
  - local images,
  - remote image URLs.
- Skill slash commands can be meaningful with empty text because the skill selection lives in `mention_bindings`.

New content definition:

```rust
!text.is_empty()
    || !local_images.is_empty()
    || !remote_image_urls.is_empty()
    || !text_elements.is_empty()
    || !mention_bindings.is_empty()
```

### 7.14 codex-rs/tui/src/chatwidget/input_submission.rs

Change:

- Replaced duplicated empty-message checks with `user_message.has_content()`.

Reason:

- Prevent bare skill invocations from being dropped as empty messages.
- Centralize message content semantics so future attachment or structured-input fields do not require every caller to remember the full list.

Existing related behavior reused:

- This file already strips `skill://` from mention binding paths before matching loaded skills.
- This file already emits `UserInput::Skill` for matched skill paths.

### 7.15 codex-rs/tui/src/chatwidget/skills.rs

Change:

- Copied `skill.argument_hint.clone()` when converting app-server protocol skill metadata back into core skill metadata for TUI use.

Reason:

- The command popup uses TUI-local `SkillMetadata`.
- Without this copy, hints loaded by app-server would be lost before popup rendering.

### 7.16 Test-Only Struct Initializer Updates

Files:

```text
codex-rs/core-skills/src/injection_tests.rs
codex-rs/core-skills/src/invocation_utils_tests.rs
codex-rs/core-skills/src/manager_tests.rs
codex-rs/core-skills/src/render.rs
codex-rs/core/src/session/tests.rs
codex-rs/tui/src/bottom_pane/mod.rs
codex-rs/tui/src/chatwidget/tests/composer_submission.rs
codex-rs/tui/src/chatwidget/tests/helpers.rs
```

Change:

- Added `argument_hint: None` to direct `SkillMetadata` or `SkillSummary` test initializers.
- Added match arms for unexpected `InputResult::SkillCommand` in existing slash command tests.

Reason:

- The metadata struct expanded.
- Existing tests should keep asserting their original behavior and fail clearly if they unexpectedly receive a skill command.

## 8. Data Model Additions

### 8.1 SkillMetadata.argument_hint

Location:

```text
codex-rs/core-skills/src/model.rs
```

Purpose:

- Stores a compact user-facing argument usage hint loaded from skill frontmatter.

### 8.2 SkillSlashCommand

Location:

```text
codex-rs/tui/src/bottom_pane/slash_commands.rs
```

Fields:

```rust
pub(crate) struct SkillSlashCommand {
    pub(crate) name: String,
    pub(crate) description: String,
    pub(crate) argument_hint: Option<String>,
    pub(crate) path: std::path::PathBuf,
}
```

Purpose:

- A TUI-specific command representation derived from `SkillMetadata`.
- It is intentionally smaller than full `SkillMetadata`.

### 8.3 SlashCommandItem.Skill

Location:

```text
codex-rs/tui/src/bottom_pane/slash_commands.rs
```

Purpose:

- Lets all slash lookup APIs return skills in the same enum as built-ins and service-tier commands.

### 8.4 CommandItem.Skill

Location:

```text
codex-rs/tui/src/bottom_pane/command_popup.rs
```

Purpose:

- Lets the command popup render and select skill commands.

### 8.5 InputResult.SkillCommand

Location:

```text
codex-rs/tui/src/bottom_pane/chat_composer.rs
```

Purpose:

- Carries a parsed skill command from composer to ChatWidget dispatch.

### 8.6 UserMessage.has_content

Location:

```text
codex-rs/tui/src/chatwidget/user_messages.rs
```

Purpose:

- Treats structured fields such as mention bindings as meaningful content.
- Prevents empty-text skill invocations from being dropped.

## 9. Compatibility and Merge Notes

### 9.1 Upstream Conflict Hotspots

Expect future upstream conflicts in these areas:

- `codex-rs/core-skills/src/model.rs`
- `codex-rs/core-skills/src/loader.rs`
- `codex-rs/protocol/src/protocol.rs`
- `codex-rs/app-server-protocol/src/protocol/v2/plugin.rs`
- `codex-rs/tui/src/bottom_pane/slash_commands.rs`
- `codex-rs/tui/src/bottom_pane/command_popup.rs`
- `codex-rs/tui/src/bottom_pane/chat_composer.rs`
- `codex-rs/tui/src/chatwidget/slash_dispatch.rs`
- `codex-rs/tui/src/chatwidget/input_submission.rs`

These are active upstream surfaces because Codex regularly changes skills, app-server protocol, and TUI input handling.

### 9.2 Why the Patch Reuses Existing Skill Mentions

The patch deliberately avoids inventing a separate skill invocation protocol.

Benefits:

- less code,
- fewer serialization changes,
- existing duplicate-name handling is preserved,
- existing disabled-skill handling is preserved,
- existing `UserInput::Skill` downstream behavior is preserved,
- fewer merge conflicts with future upstream backend changes.

### 9.3 Known Limitations

Known limitations in the current patch:

- Skill names that collide with built-in slash commands resolve to the built-in command.
- Remote plugin catalog skills do not expose `argument_hint`; they currently use `None`.
- The npm package and CLI binary are still named as upstream Codex.
- No upstream sync workflow has been added yet.
- No publish workflow for `happycodex` has been added yet.

### 9.4 Future Work

Recommended next steps:

1. Rename npm package metadata to `happycodex`.
2. Rename optional platform packages.
3. Update `codex-cli/bin/codex.js` package lookup names and reinstall messages.
4. Update release staging scripts to publish HappyCodex package names.
5. Add a GitHub Actions upstream sync workflow.
6. Add a manual publish workflow.
7. Add a fork changelog section for each downstream patch.
8. Add integration tests for slash-invoked skills producing `UserInput::Skill`.

## 10. Validation Notes

### 10.1 Tests Added

New direct tests in this patch:

- `parses_skill_argument_hint_frontmatter`
- `derives_skill_argument_hint_from_arguments_frontmatter`
- `skill_commands_are_exposed_and_support_inline_args`
- `skill_commands_participate_in_prefix_matching`
- `skill_command_displays_argument_hint_in_description`

### 10.2 Tests Updated

Existing tests were updated to compile against the expanded metadata model and to keep explicit panic branches for unexpected skill command dispatch.

Affected categories:

- skill loader tests,
- skill injection tests,
- skill invocation utility tests,
- skill manager tests,
- skill render tests,
- session skill metadata tests,
- bottom pane tests,
- chatwidget composer submission tests,
- plugin helper tests.

### 10.3 Tests Not Run During Fork Setup

During the fork setup turn, tests were not run. That turn only:

- rewired remotes,
- created the downstream branch,
- committed the existing patch,
- pushed it to `happyskillsai/happycodex`.

Before publishing a HappyCodex npm package, run at least:

```bash
cargo test -p codex-core-skills
cargo test -p codex-tui
cargo test -p codex-app-server-protocol
cargo check --workspace
```

The exact package names may need adjustment if upstream renames workspace packages.
