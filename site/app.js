async function hydrateBuild() {
  const status = document.querySelector("#build-status");
  const buildQuery = new URL(document.querySelector("#token-stylesheet").href).search;
  try {
    const [buildResponse, tokenResponse] = await Promise.all([
      fetch(`assets/build.json${buildQuery}`, { cache: "no-store" }),
      fetch(`assets/flattened-tokens.json${buildQuery}`, { cache: "no-store" }),
    ]);
    const build = await buildResponse.json();
    const tokens = await tokenResponse.json();
    status.textContent = `${build.tokenCount} tokens · ${build.commit}`;
    document.querySelector("#storybook-link").hidden = !build.storybook;
    document.querySelector("#core-value").textContent = tokens["brand.500"].$value;
    document.querySelectorAll("[data-token]").forEach((element) => {
      const item = tokens[element.dataset.token];
      if (item) element.textContent = item.$value;
    });
  } catch (error) {
    status.textContent = "Generated assets unavailable";
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

hydrateBuild();
