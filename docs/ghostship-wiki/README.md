# Ghostship Wiki

This is the image-managed seed for `/home/hermes/ghostship-wiki`.

The container boot process copies these files into Hermes' home on every boot and
overwrites the repo-managed files listed in `.ghostship-managed-files`. Agent-created
files are preserved as long as they live outside the managed source tree.

Use this wiki as a reference, not a workflow skill. It should tell Hermes what
APIs, tools, environment variables, and image contracts exist so the agent can
choose its own workflow and write task-specific code when needed.
