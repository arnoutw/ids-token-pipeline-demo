# IDS Token Pipeline Demo

A small reconstruction of the design-token workflow with one **Brand Primary** button, four states and two demo brands. Both brands use the same semantic tokens and Button CSS. Brand A keeps the original purple palette. Brand B is a fictional teal palette for this exercise.

- Repository: <https://github.com/arnoutw/ids-token-pipeline-demo>
- Demo page: <https://arnoutw.github.io/ids-token-pipeline-demo/>
- Storybook: <https://arnoutw.github.io/ids-token-pipeline-demo/storybook/?path=/story/ids-brand-primary-button--interactive>

## What is included

- Figma file: [IDS Token Pipeline Demo](https://www.figma.com/design/oSw8jYUHN4wuXkYFELq7l1)
- `Core` Figma variable collection with Brand A and Brand B modes, and one `Semantic` collection with shared aliases
- `Button / Brand Primary` with Default, Hover, Focused, and Pressed variants
- one Tokens Studio single-file source at `tokens/tokens.json`
- a dependency-free Python build that validates both brands and creates standalone CSS and JSON for each
- a one-page component documentation site
- a Storybook with the same Button styles and generated tokens, including the Accessibility panel
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

To build the whole site, including Storybook, use Node 24, pnpm and Python 3:

```bash
pnpm install --frozen-lockfile
pnpm run build
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist/site
```

Open <http://127.0.0.1:8000/>. For Storybook development on its own, run `pnpm run storybook`. Restart it after changing the source tokens so the CSS is regenerated.

## Propose a token change

The demo uses a Tokens Studio single-file export. Git is the build and release source. Figma is where design authors and reviews the proposal. The build selects one `Core/Brand A` or `Core/Brand B` set and combines it with `Semantic/Value`.

1. Start a branch from `main`. In Figma, select the `Core` mode for the brand you want to change and edit `brand/500`. Keep the other mode unchanged. In the comparison frame, check the states using the changed brand alongside the other brand.
2. Import Figma Variables into Tokens Studio and inspect the imported sets. The expected keys are `Core/Brand A`, `Core/Brand B` and `Semantic/Value`. If the plugin creates duplicate sets or imports dimensions differently, export the JSON and review and reconcile it against `tokens/tokens.json` on the branch. The plugin workflow depends on the plan and the file's existing theme mappings.
3. Use the GitHub sync provider with these settings, or commit the reviewed JSON on the branch.

   | Field | Value |
   |---|---|
   | Name | `IDS demo` |
   | Personal access token | a GitHub token with access to this repository |
   | Repository | `arnoutw/ids-token-pipeline-demo` |
   | Branch | your token change branch |
   | Token storage | `tokens/tokens.json` |
   | Base URL | leave blank for github.com |

4. Open a pull request. Review the token diff and use the Actions preview to check both brands. In Storybook, use the Brand toolbar in **Interactive** and use **Compare Brands** to view the states together. Tab to the button to check real focus. The Accessibility panel provides automated checks for the selected story.

Do not put the personal access token in Figma text, this repository, or the demo page.

Both brands use the same token chain.

```text
Core / Brand A or Brand B / brand/500
    ↓
Semantic.interactive-primary-brand.enabled
    ↓
--interactive-primary-brand-enabled
    ↓
.ids-button
```

## Consume a brand

GitHub Actions produces a separate `ids-brand-a-<sha>` and `ids-brand-b-<sha>` download per successful build, including pull requests. Pick the desired brand from a reviewed commit. Each download contains `tokens.css`, resolved `tokens.json`, the shared `button.css`, and build provenance in `build.json`. Load `tokens.css` before `button.css` and use the same `<button class="ids-button" type="button">Continue</button>` markup. Each brand CSS file is standalone and sets its values on `:root`.

The preview uses the combined `dist/site/assets/tokens.css` with `data-brand` scopes so both brands can appear together. `dist/site/assets/themes/<brand>/` holds the standalone outputs. The older `flattened-tokens.json` URL remains the Brand A snapshot. GitHub Pages serves the latest demo after a successful build on `main`.

## Ownership and releases

- **Brand changes** are proposed and reviewed by the brand owner. The design-system maintainer reviews the impact on shared aliases and checks the other brand in the preview.
- **Shared changes** to token names, states or Button CSS belong to the design-system maintainers. Review with the affected consumers and document migrations for breaking changes. A change to the name or type of a shared token is a contract change.
- **Automated checks** resolve aliases for each brand independently, reject duplicate CSS names and token contract mismatches, check label contrast in the four states and ring contrast against the demo surfaces, then build Storybook. These checks cover the demo surfaces. Product teams test their actual backgrounds, keyboard behaviour and kiosk hardware as appropriate.
- **Production setup** would protect `main` with required PR reviews and build checks, and assign actual reviewers with `CODEOWNERS`. This compact single-file export has one review boundary. Split shared and per-brand source sets into separate paths when brand teams need independent code ownership. Use tagged, versioned packages or immutable release assets for consumption, with changelogs and dependency pinning for rollback. Actions downloads are review artifacts, and Pages hosts the demo.

To view a PR build, extract the `ids-preview-pr-…` Actions artifact and serve the extracted folder with `python3 -m http.server 8000 --bind 127.0.0.1`. The same output is available locally with `pnpm run build`.

## Scope and provenance

This is a miniature demo, not a copy of the full historical Irdeto design system or its internal CI/CD implementation. It uses a small subset of Brand Primary values and the public IDS token naming pattern so the end-to-end concept is easy to explain live.
