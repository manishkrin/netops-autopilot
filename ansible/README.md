# Ansible workflows

Month 5 will add allow-listed diagnostic and remediation playbooks here. A workflow will not be runnable by the application until it has:

- a stable workflow identifier and checksum
- constrained, schema-validated variables
- an idempotency strategy
- least-privilege lab credentials supplied outside the repository
- pre-check and post-change verification
- timeout and partial-failure behavior
- a tested rollback workflow
- policy and human-approval integration

No employer playbooks, inventories, secrets, or device data belong here.

