# neuroarchitectures.github.io

The documentation website for the **Neuroarchitectures** community — home of the **Neural Architecture Exchange Specification (NAXS)**.

**Live site:** <https://neuroarchitectures.github.io>

```bash
npm install
npm run dev      # local dev server with hot reload
npm run build    # static export to site.zip (used by CI)
```

## Stack

- [Mintlify](https://mintlify.com) docs framework (`docs.json` + MDX pages)
- CI runs `mintlify export` (static, air-gapped output), unzips it, and publishes the result to **GitHub Pages**

## Content sources

- Specification pages under `specification/` are generated from [`naxs/specification.md`](https://github.com/neuroarchitectures/naxs/blob/main/specification.md) by `scripts/split_spec.py`. Re-run the script when the upstream spec changes:

  ```bash
  python3 scripts/split_spec.py ../naxs/specification.md
  ```

- Example documents in `snippets/examples/` are copies of the [canonical examples](https://github.com/neuroarchitectures/naxs/tree/main/naxs/v1.0/examples) in the spec repo.

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds the site and publishes it to GitHub Pages at <https://neuroarchitectures.github.io>.

## License

- Documentation text: CC-BY-4.0
- Code and configuration: Apache-2.0
