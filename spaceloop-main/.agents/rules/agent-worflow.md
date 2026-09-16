---
trigger: always_on
---

# SpaceLoop Agent Workflow

## Before Coding

For every task:

1. Read the relevant rules.
2. Inspect only the files relevant to the task.
3. Search for existing implementations before creating new ones.
4. Reuse existing utilities and abstractions where appropriate.

Do NOT scan or rewrite the entire repository unless the task genuinely requires it.

## Implementation

Work incrementally.

Make the smallest coherent change that solves the requested task.

Do not modify unrelated files.

Do not refactor unrelated code.

Do not add unnecessary dependencies.

Do not create duplicate implementations.

## Testing

After implementation:

1. Run the smallest relevant test set first.
2. Fix issues caused by the current change.
3. Run broader tests when appropriate.

Do not repeatedly run the entire test suite after every small edit.

## Communication

Keep responses concise.

Report:

- what changed
- tests run
- test result
- remaining issue, if any

Do not provide lengthy explanations unless requested.

## Stopping Rule

If the requested task is complete, STOP.

Do not proactively implement the next phase.

Do not redesign unrelated architecture.

Do not make speculative improvements.