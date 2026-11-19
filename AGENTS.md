# ER-MailTool: project instructions

- Read [README.md](README.md) for the product overview, operation, diagnostics and release process.
- Keep the desktop GUI, CLI, API and standalone builds compatible; do not change release automation or versions incidentally.
- Follow the existing CustomTkinter theme and views. Keep network operations off the GUI thread.
- Use the Python standard library and existing dependencies where practical. Do not log credentials or tokens.
- Run relevant tests and `poetry run ruff check .`; document user-visible changes in the README.
- The [ER KnowledgeBase](https://github.com/Eidolf/ER-KnowledgeBase) is a separate, access-controlled project.
  No MailTool-specific profile was identified in the checked local snapshot; do not invent one or copy private content.
