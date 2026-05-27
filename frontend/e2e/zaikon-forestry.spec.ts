import { expect, Page, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const API_BASE = process.env.ZAIKON_E2E_API_BASE ?? "http://127.0.0.1:8100";
const FORESTRY_DIR =
  process.env.ZAIKON_E2E_FORESTRY_DIR ?? "D:\\POSAO\\OllamaProjects\\ZAIKON\\DOCUMENTS\\šumarstvo";

test.describe.configure({ mode: "serial" });

test.describe("zAIkon forestry end-to-end workflow", () => {
  test("imports forestry PDFs and follows the workflow through every UI area", async ({ page, request }) => {
    test.setTimeout(10 * 60 * 1000);
    const corpusName = `E2E Šumarstvo ${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}`;
    let draftRunId = "";

    await test.step("Preflight: servers and forestry PDF folder are available", async () => {
      const health = await request.get(`${API_BASE}/health`);
      expect(health.ok(), `Backend health endpoint must respond at ${API_BASE}`).toBeTruthy();
      expect(fs.existsSync(FORESTRY_DIR), `Missing forestry fixture folder: ${FORESTRY_DIR}`).toBeTruthy();
      expect(findFirstPdf(FORESTRY_DIR), "Forestry folder should contain at least one PDF").toBeTruthy();
    });

    await test.step("Create corpus and import the forestry folder", async () => {
      await page.goto("/corpora");
      await expect(page.getByRole("heading", { name: "Korpusi" })).toBeVisible();
      const createCorpusForm = page.locator("form").filter({ has: page.getByRole("button", { name: "Kreiraj korpus" }) });
      await createCorpusForm.getByRole("textbox", { name: "Naziv" }).fill(corpusName);
      await createCorpusForm.getByRole("textbox", { name: "Opis" }).fill("Automatski E2E korpus za šumarstvo PDF set");
      await createCorpusForm.getByRole("button", { name: "Kreiraj korpus" }).click();

      await chooseCorpus(page, corpusName);
      await page.getByLabel("Lokalni folder").fill(FORESTRY_DIR);
      await page.getByRole("button", { name: "Pokreni import" }).click();
      await expect(page.locator("summary").filter({ hasText: "Import report" })).toBeVisible({ timeout: 240_000 });
      await expect(page.getByRole("heading", { name: "Trag obrade" })).toBeVisible();
      await expect(page.getByText("Indeksiranje").first()).toBeVisible();
      await openFirstArtifact(page);
    });

    await test.step("Open imported documents and inspect legal structure", async () => {
      await page.goto("/documents");
      await chooseCorpus(page, corpusName);
      await page.getByRole("button", { name: "Učitaj dokumente iz izabranog korpusa" }).click();
      await expect(page.locator(".list .list-item").first()).toBeVisible({ timeout: 90_000 });
      await page.locator(".list .list-item").first().click();
      await expect(page.getByText("Detalj dokumenta")).toBeVisible();
      await expect(page.getByRole("link", { name: "Akoma" })).toBeVisible();
      await expect(page.getByText("Trag obrade")).toBeVisible();
    });

    await test.step("Run relevant hybrid searches against the forestry corpus", async () => {
      await page.goto("/search");
      await chooseCorpus(page, corpusName);
      await page.getByLabel("Upit").fill("gazdovanje šumama evidencija seča");
      await page.getByLabel("top_k").fill("5");
      await page.getByRole("button", { name: "Pretraži" }).click();
      await expect(page.getByText("Hybrid retrieval")).toBeVisible({ timeout: 90_000 });
      await expect(page.locator(".result-card").first()).toBeVisible();

      await page.getByLabel("Upit").fill("šumsko zemljište zaštita i prenamena");
      await page.getByRole("button", { name: "Pretraži" }).click();
      await expect(page.locator(".result-card").first()).toBeVisible({ timeout: 90_000 });
    });

    await test.step("Create and run a draft review from a realistic forestry draft", async () => {
      await page.goto("/draft-reviews");
      await chooseCorpus(page, corpusName);
      const createDraftForm = page.locator("form").filter({ has: page.getByRole("button", { name: "Kreiraj i pokreni proveru" }) });
      await createDraftForm.getByRole("textbox", { name: "Naslov" }).fill("E2E nacrt pravilnika o šumama");
      await createDraftForm.getByLabel("Tekst").fill([
        "NACRT PRAVILNIKA O EVIDENCIJI I KORIŠĆENJU ŠUMA",
        "",
        "Član 1.",
        "Ovim pravilnikom uređuje se evidencija seče šuma i obaveze korisnika šuma.",
        "",
        "Član 2.",
        "Šumsko zemljište se može prenameniti bez posebne saglasnosti nadležnog organa.",
        "",
        "Član 3.",
        "Nadležni organ ne vodi javnu evidenciju izdatih odobrenja za seču."
      ].join("\n"));
      await createDraftForm.getByRole("button", { name: "Kreiraj i pokreni proveru" }).click();
      await expect(page.getByText("Pokrećem analizu nacrta").or(page.getByText("Analiza je završena"))).toBeVisible({ timeout: 90_000 });
      await expect(page.getByRole("button", { name: "Ponovo pokreni" })).toBeVisible({ timeout: 180_000 });

      const akomaHref = await page.getByRole("link", { name: "Akoma" }).getAttribute("href");
      draftRunId = akomaHref?.match(/draft-reviews\/([^/]+)\/akoma-ntoso/)?.[1] ?? "";
      expect(draftRunId, "Draft run id should be visible through the Akoma link").toBeTruthy();

      await expect(page.locator(".mini-list").getByRole("heading", { name: "Nalazi" })).toBeVisible({ timeout: 180_000 });
      await expect(page.getByText("Trag obrade")).toBeVisible();
      await openFirstArtifact(page);
    });

    await test.step("Review findings and record a reviewer decision when findings exist", async () => {
      await page.goto("/findings");
      await page.getByLabel("pipeline_run_id").fill(draftRunId);
      await page.getByRole("button", { name: "Filtriraj" }).click();
      await expect(page.getByRole("button", { name: "Filtriraj" })).toBeEnabled({ timeout: 90_000 });
      await expect(page.locator(".picker-meta").getByText(/nalaza/)).toBeVisible({ timeout: 90_000 });
      const findingRows = page.locator("tbody tr:has(td)");
      if (await findingRows.count()) {
        const firstFinding = findingRows.first();
        await expect(firstFinding).toBeVisible();
        await firstFinding.click();
        await page.getByLabel("Napomena recenzenta").fill("E2E pregled: potrebno pravničko usaglašavanje sa propisima o šumama.");
        await page.getByRole("button", { name: "Ekspert" }).click();
        await expect(page.getByRole("button", { name: "Filtriraj" })).toBeEnabled({ timeout: 90_000 });
        await expect(page.locator(".error-box")).toHaveCount(0);
      }
    });

    await test.step("Generate DOCX and PDF reports for the draft run", async () => {
      await page.goto("/reports");
      await generateReport(page, draftRunId, "docx");
      await generateReport(page, draftRunId, "pdf");
      await page.getByPlaceholder("report_id, pipeline_run_id, naslov...").fill(draftRunId);
      await expect(page.getByText(draftRunId.slice(0, 8))).toBeVisible({ timeout: 90_000 });
      await expect(page.getByRole("link", { name: "Preuzmi" }).first()).toBeVisible();
    });

    await test.step("Ask the assistant a cited forestry question", async () => {
      await page.goto("/assistant");
      await chooseCorpus(page, corpusName);
      const createSessionForm = page.locator("form").filter({ has: page.getByRole("button", { name: "Kreiraj sesiju" }) });
      await createSessionForm.getByRole("textbox", { name: "Naslov" }).fill("E2E asistent šumarstvo");
      await createSessionForm.getByRole("button", { name: "Kreiraj sesiju" }).click();
      await expect(page.getByText(/Aktivna sesija: (?!nema)/)).toBeVisible({ timeout: 90_000 });
      await page.getByPlaceholder("Postavi pravno pitanje...").fill("Koje obaveze postoje za evidenciju seče i gazdovanje šumama?");
      await page.getByRole("button", { name: "Pošalji" }).click();
      await expect(page.locator(".message-list .message").last()).toBeVisible({ timeout: 180_000 });
      await expect(page.getByText("Pronalaženje citata").first()).toBeVisible();
    });
  });
});

async function chooseCorpus(page: Page, corpusName: string) {
  await page.getByLabel("Pretraga korpusa").first().fill(corpusName);
  const row = page.getByRole("row", { name: new RegExp(escapeRegex(corpusName), "i") }).first();
  await expect(row).toBeVisible({ timeout: 60_000 });
  await row.click();
}

async function openFirstArtifact(page: Page) {
  const artifactButton = page.locator(".link-button, .artifact-tabs button").first();
  if (await artifactButton.isVisible()) {
    await artifactButton.click();
    await expect(page.locator("summary").filter({ hasText: /Output artefakta|Debug JSON/ }).first()).toBeVisible({ timeout: 60_000 });
  }
}

async function generateReport(page: Page, runId: string, format: "docx" | "pdf") {
  const form = page.locator("form").filter({ has: page.getByRole("button", { name: "Generiši" }) });
  await form.getByLabel("pipeline_run_id").fill(runId);
  await form.getByLabel("Format").selectOption(format);
  await form.getByRole("button", { name: "Generiši" }).click();
  await expect(page.getByText("Lista izveštaja")).toBeVisible({ timeout: 90_000 });
}

function findFirstPdf(folder: string): string | null {
  const entries = fs.readdirSync(folder, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(folder, entry.name);
    if (entry.isFile() && entry.name.toLowerCase().endsWith(".pdf")) return fullPath;
    if (entry.isDirectory()) {
      const nested = findFirstPdf(fullPath);
      if (nested) return nested;
    }
  }
  return null;
}

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
