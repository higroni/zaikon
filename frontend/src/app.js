const apiBaseInput = document.querySelector("#apiBase");

function apiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
}

async function request(path, options = {}) {
  const response = await fetch(`${apiBase()}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(payload?.detail || response.statusText);
  }
  return payload;
}

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

document.querySelector("#corpusForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const output = document.querySelector("#corpusOutput");
  const data = new FormData(event.currentTarget);
  output.textContent = "Import u toku...";
  try {
    const created = await request("/api/v1/corpora", {
      method: "POST",
      body: JSON.stringify({ name: data.get("name") }),
    });
    const imported = await request(
      `/api/v1/corpora/${created.corpus.corpus_id}/import-folder`,
      {
        method: "POST",
        body: JSON.stringify({
          corpus_id: created.corpus.corpus_id,
          folder_uri: data.get("folder_uri"),
        }),
      },
    );
    output.textContent = pretty(imported);
  } catch (error) {
    output.textContent = error.message;
  }
});

document.querySelector("#searchForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const resultsNode = document.querySelector("#searchResults");
  const data = new FormData(event.currentTarget);
  resultsNode.textContent = "Pretraga...";
  try {
    const payload = {
      query: data.get("query"),
      top_k: 8,
    };
    if (data.get("corpus_id")) {
      payload.corpus_id = data.get("corpus_id");
    }
    const response = await request("/api/v1/search/hybrid", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    resultsNode.innerHTML = response.results
      .map(
        (result) => `
          <article class="result">
            <strong>${result.filename}</strong> ${result.path}
            <div>Score: ${result.score.toFixed(3)}</div>
            <p>${result.content_text}</p>
          </article>
        `,
      )
      .join("");
  } catch (error) {
    resultsNode.textContent = error.message;
  }
});

document.querySelector("#draftForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const output = document.querySelector("#draftOutput");
  const data = new FormData(event.currentTarget);
  output.textContent = "Provera u toku...";
  try {
    const payload = {
      title: data.get("title"),
      content_text: data.get("content_text"),
    };
    if (data.get("selected_corpus_id")) {
      payload.selected_corpus_id = data.get("selected_corpus_id");
    }
    const created = await request("/api/v1/draft-reviews", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const run = await request(
      `/api/v1/draft-reviews/${created.draft_review.pipeline_run_id}/run`,
      { method: "POST", body: "{}" },
    );
    output.textContent = pretty(run);
  } catch (error) {
    output.textContent = error.message;
  }
});
