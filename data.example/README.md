# data.example

This directory is a template for your private corpus. Copy it to `data/` and edit the markdown files:

```bash
cp -r data.example data
docker compose run --rm backend python -m scripts.seed
```

`data/` is gitignored. Keep your resume, project notes, and any personal details there; they are not pushed to GitHub.

Each `data/documents/*.md` file becomes one document. Use clear headings and short sections so the agent can retrieve relevant pieces.
