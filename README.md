# IDS Token Pipeline Demo

A small reconstruction of the design-token workflow with one **Brand Primary** button, four states and two fictional brands. Both use the same semantic tokens and Button CSS. Brand A uses purple and Montserrat. Brand B uses teal and Source Sans 3.

- Repository: <https://github.com/arnoutw/ids-token-pipeline-demo>
- Demo page: <https://arnoutw.github.io/ids-token-pipeline-demo/>
- Storybook: <https://arnoutw.github.io/ids-token-pipeline-demo/storybook/?path=/story/ids-brand-primary-button--interactive>

## What is included

- Figma file: [IDS Token Pipeline Demo](https://www.figma.com/design/oSw8jYUHN4wuXkYFELq7l1)
- `Core` Figma variable collection with Brand A and Brand B modes, a `Platform` collection with Web, Kiosk and Onboard modes, and one `Semantic` collection with shared aliases
- `Button / Brand Primary` with Default, Hover, Focused, and Pressed variants
- reusable `State caption` instances above the buttons in the Figma comparison, with captions generated from the sample states in Storybook
- one Tokens Studio single-file source at `tokens/tokens.json`
- a dependency-free Python build that validates both token contracts and creates CSS and JSON for every brand and platform combination
- a one-page component documentation site
- a Storybook with the platform comparison, interactive Kiosk and Onboard examples, and the native Code and Accessibility panels
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

The demo uses Tokens Studio's single-file format. Git is the build and release source. Figma is where designers author and review the proposal. The build combines `Core` and `Semantic` tokens for each brand and selects platform dimensions independently.

1. Start a branch from `main`. In Figma, select the `Core` mode for the brand you want to change and edit `brand/500`. Keep the other mode unchanged. In the comparison frame, check the states using the changed brand alongside the other brand.
2. In Tokens Studio, choose **Styles & Variables → Import variables**. Select both Core modes, all three Platform modes and the Semantic collection. Enable **Convert numbers to dimensions**, review the import and choose **Import all**.
3. Without Tokens Studio branching, choose **Load and export → Export to file/folder → Single file**, then enable **All token sets** and **Include parent key**. Reconcile the export with `tokens/tokens.json` and commit the reviewed changes on the branch. Button spacing belongs to the Platform sets. If the export still includes the old Core spacing variables from the Figma file, leave those entries out of the reviewed JSON to avoid duplicate CSS names.

   With Tokens Studio branching enabled, you can also sync directly to the review branch using this provider configuration.

   | Field | Value |
   |---|---|
   | Name | `IDS demo` |
   | Personal access token | a GitHub token with access to this repository |
   | Repository | `arnoutw/ids-token-pipeline-demo` |
   | Branch | your token change branch |
   | Token storage | `tokens/tokens.json` |
   | Base URL | leave blank for github.com |

4. Open a pull request. Review the token diff and check all six combinations in Storybook's **Compare Platforms**. Use **Kiosk Touch** and **Onboard Navigation** to try each brand from the toolbar. The Code tab shows the markup, and the Accessibility tab runs automated checks for the selected story.

Do not put the personal access token in Figma text, this repository, or the demo page.

Both brands use the same token chain.

```text
Core / Brand A or Brand B / brand/500
    ↓
Semantic.button.primary.background.default
    ↓
--button-primary-background-default
    ↓
.ids-button
```

Under `button/primary`, each background state has its own token. The label and ring colours use `text` and `focus-ring`. The ring is 3px on web and kiosk and 5px on onboard, with a 2px gap. Leave at least 7px of clearance wherever an ancestor clips content. The build checks the ring colour against the light surfaces in the demo.

The same `typography/control/font-family` role resolves to `font/family/ui` in the active brand mode. Web, Kiosk and Onboard each set their own minimum size, padding, text size, line height and focus ring width. The documentation captions use a common style and sit next to the button instances in the specimen. Figma may import font-family variables as generic text tokens. Keep `$type: "fontFamily"` when reconciling them so the CSS build quotes multiword family names correctly.

The demo uses 48px, 64px and 56px minimum heights for Web, Kiosk and Onboard. These are demo values. Product teams validate hit areas, contrast, text fit and focus on their actual devices. The kiosk simulates a print action. The onboard example supports touch and demonstrates directional focus between two buttons with arrow keys and native Enter or Space activation.

## Consume a brand

GitHub Actions produces a separate `ids-brand-a-<sha>` and `ids-brand-b-<sha>` download per successful build, including pull requests. Each brand archive contains `button.css` and the files below.

| Path | What to use it for |
| --- | --- |
| `tokens.css` | Brand defaults plus platform overrides selected with `data-platform` |
| `tokens.json` | Resolved brand and Web defaults |
| `platforms/{web,kiosk,onboard}/tokens.css` | A standalone brand and platform combination on `:root` |
| `platforms/{web,kiosk,onboard}/tokens.json` | Resolved values for a particular brand and platform |
| `build.json` | Commit and build information, included at the brand and platform levels |

Load the chosen `tokens.css` before the shared `button.css`. When using the first CSS option, select the platform on the enclosing element.

```html
<div data-platform="kiosk">
  <button class="ids-button" type="button">Print boarding pass</button>
</div>
```

Load the chosen webfont at weight 500 in the consuming app. The demo and Storybook load both fonts for comparison. In a production rollout, confirm font licensing and supported languages with the brand team and agree on hosted font assets, including offline delivery for kiosks where required.

The preview uses the combined `dist/site/assets/tokens.css` with independent `data-brand` and `data-platform` scopes. `dist/site/assets/themes/<brand>/` holds the standalone outputs. `flattened-tokens.json` is the Brand A Web snapshot. GitHub Pages serves the latest demo after a successful build on `main`.

## Ownership and releases

- **Brand changes** are proposed and reviewed by the brand owner. The design-system maintainer reviews the impact on shared aliases and checks the other brand in the preview.
- **Platform changes** are reviewed by the device team and the design-system maintainer. Both brands inherit the platform values, so both are checked before release.
- **Shared changes** to token names, states or Button CSS belong to the design-system maintainers. Review with the affected consumers and document migrations for breaking changes. A change to the name or type of a shared token is a contract change.
- **Automated checks** resolve aliases for each brand independently, reject duplicate CSS names and token contract mismatches, check label contrast in the four states and ring contrast against the demo surfaces, then build Storybook. These checks cover the demo surfaces. Product teams test their actual backgrounds, keyboard behaviour and kiosk hardware as appropriate.
- **Production setup** would protect `main` with required PR reviews and build checks, and assign actual reviewers with `CODEOWNERS`. This compact single-file export has one review boundary. Split shared and per-brand source sets into separate paths when brand teams need independent code ownership. Use tagged, versioned packages or immutable release assets for consumption, with changelogs and dependency pinning for rollback. Actions downloads are review artifacts, and Pages hosts the demo.

To view a PR build, extract the `ids-preview-pr-…` Actions artifact and serve the extracted folder with `python3 -m http.server 8000 --bind 127.0.0.1`. The same output is available locally with `pnpm run build`.

## Scope and provenance

This is a miniature demo, not a copy of the full historical Irdeto design system or its internal CI/CD implementation. It uses a small subset of Brand Primary values and the public IDS token naming pattern so the end-to-end concept is easy to explain live.
