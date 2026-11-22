# IDS Token Pipeline Demo

A deliberately small reconstruction of the design-token workflow: one **Brand Primary** button, four states, and a traceable path from Figma variables to generated CSS and flattened JSON.

- Repository: <https://github.com/arnoutw/ids-token-pipeline-demo>
- Demo page: <https://arnoutw.github.io/ids-token-pipeline-demo/>

## What is included

- Figma file: [IDS Token Pipeline Demo](https://www.figma.com/design/oSw8jYUHN4wuXkYFELq7l1)
- `Core` and `Semantic` Figma variable collections with aliases
- `Button / Brand Primary` with Default, Hover, Focused, and Pressed variants
- one Tokens Studio single-file source at `tokens/tokens.json`
- a dependency-free Python build that creates `tokens.css` and `flattened-tokens.json`
- a one-page component documentation site
- GitHub Actions deployment to GitHub Pages
- a local demo runner for macOS

## Run locally

Double-click **Start Demo.command**, or run:

```bash
python3 scripts/dev.py
```

The runner builds the token output, opens <http://127.0.0.1:8000>, and rebuilds when the source changes. Refresh the browser after a rebuild.

For a one-off build:

```bash
python3 scripts/build.py
```

## Tokens Studio setup

The free Tokens Studio plan can use a single JSON file, which keeps this demo intentionally small.

1. Open the Tokens Studio plugin in the Figma file.
2. Start with a new empty token file.
3. Choose **Import → Variables → Import all**. This creates tokens attached to the native Figma variables.
4. Add a GitHub sync provider with:

   | Field | Value |
   |---|---|
   | Name | `IDS demo` |
   | Personal access token | a GitHub token with access to this repository |
   | Repository | `arnoutw/ids-token-pipeline-demo` |
   | Branch | `main` |
   | Token storage | `tokens/tokens.json` |
   | Base URL | leave blank for github.com |

5. Push from Tokens Studio. The first push may replace the seed JSON with the plugin's equivalent single-file structure; the build accepts both `$value`/`$type` and legacy `value`/`type` token syntax.

Do not put the personal access token in Figma text, this repository, or the demo page.

## Thursday demo flow

1. Show the button states and generated artifacts on the documentation page.
2. In Figma, change **Core → brand → 500**.
3. In Tokens Studio, use **Import → Variables → Existing tokens → Update all**.
4. Push `tokens/tokens.json` to `main`.
5. Open the GitHub Actions run and wait for the Pages deployment.
6. Refresh the documentation page. The Default button and the `brand/500` swatch now use the new value.

The semantic token remains stable:

```text
Core.brand.500
    ↓
Semantic.interactive-primary-brand.enabled
    ↓
--interactive-primary-brand-enabled
    ↓
.ids-button
```

## Build outputs

Generated into `dist/site/assets/`:

- `tokens.json` — the source synchronized by Tokens Studio
- `flattened-tokens.json` — aliases resolved for easy inspection
- `tokens.css` — CSS custom properties, preserving semantic references
- `build.json` — timestamp, commit, source, and token count

`dist/` is not committed. GitHub Actions builds it from source on every relevant push.

## Scope and provenance

This is a miniature demo, not a copy of the full historical Irdeto design system or its internal CI/CD implementation. It uses a small subset of Brand Primary values and the public IDS token naming pattern so the end-to-end concept is easy to explain live.
