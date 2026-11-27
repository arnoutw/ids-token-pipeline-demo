const picker = document.querySelector("#brand");
const platformPicker = document.querySelector("#platform");
const platformActions = { web: "Continue", kiosk: "Print boarding pass", onboard: "Play" };
const status = document.querySelector("#build-status");
const buildQuery = new URL(document.querySelector("#token-stylesheet").href).search;

async function fetchJson(path) {
  const response = await fetch(`${path}${buildQuery}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Could not load ${path}`);
  return response.json();
}

const buildRequest = fetchJson("assets/build.json");

async function showSelection() {
  const brand = picker.value;
  const name = brand === "brand-b" ? "Brand B" : "Brand A";
  const platform = platformPicker.value;
  const platformName = platformPicker.selectedOptions[0].textContent;
  const folder = `assets/themes/${brand}/platforms/${platform}`;
  document.documentElement.dataset.brand = brand;
  document.documentElement.dataset.platform = platform;
  document.querySelector("#preview-action").textContent = platformActions[platform];
  document.querySelector("#hover-sample").hidden = platform !== "web";
  for (const type of ["css", "json"]) {
    const link = document.querySelector(`#brand-${type}`);
    link.href = `${folder}/tokens.${type}`;
    link.textContent = `${name} · ${platformName} ${type.toUpperCase()}`;
  }
  try {
    const [build, tokens] = await Promise.all([
      buildRequest,
      fetchJson(`${folder}/tokens.json`),
    ]);
    if (picker.value !== brand || platformPicker.value !== platform) return;
    status.textContent = `${name} · ${platformName} · ${build.tokenCount} tokens · ${build.commit}`;
    document.querySelector("#brand-typeface").textContent = tokens["typography.control.font-family"].$value;
    document.querySelector("#platform-size").textContent = `${tokens["size.control.min-height"].$value} minimum height`;
    document.querySelector("#storybook-link").hidden = !build.storybook;
    document.querySelector("#core-value").textContent = tokens["brand.500"].$value;
    document.querySelectorAll("[data-token]").forEach((element) => {
      const item = tokens[element.dataset.token];
      if (item) element.textContent = item.$value;
    });
  } catch {
    if (picker.value === brand && platformPicker.value === platform) status.textContent = "Generated assets unavailable";
  }
}

document.querySelectorAll(".copy-button").forEach((button) => {
  button.addEventListener("click", async () => {
    const source = document.getElementById(button.dataset.copy);
    await navigator.clipboard.writeText(source.textContent);
    button.textContent = "Copied";
    window.setTimeout(() => { button.textContent = "Copy"; }, 1200);
  });
});

picker.addEventListener("change", showSelection);
platformPicker.addEventListener("change", showSelection);
showSelection();
