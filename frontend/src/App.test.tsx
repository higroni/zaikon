import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App, buildDraftTrace, buildSearchTrace, RetrievalResultCard, ReviewDecisionControls } from "./App";

describe("zAIkon GUI", () => {
  it("renders the operational navigation", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: /Korpusi/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Pretraga/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Trag obrade/i })).toBeInTheDocument();
  });

  it("builds search trace with retrieval and ranking stages", () => {
    const trace = buildSearchTrace("šume", {
      results: [{ title: "Zakon o šumama", score: 0.9, lexical_score: 0.5, semantic_score: 0.8 }]
    });
    expect(trace.map((stage) => stage.id)).toEqual(["query", "retrieval", "ranking"]);
    expect(trace[1].summary).toContain("1 pogodaka");
  });

  it("builds draft trace around available artifacts and findings", () => {
    const trace = buildDraftTrace(
      { pipeline_run_id: "run-1", title: "Nacrt", artifacts: { canonical_document: { title: "Nacrt" } } },
      ["canonical_document"],
      [{ finding_id: "f-1" }]
    );
    expect(trace.find((stage) => stage.id === "canonical_document")?.status).toBe("done");
    expect(trace.find((stage) => stage.id === "checker_findings")?.summary).toContain("1 nalaza");
  });

  it("renders retrieval result score breakdown", () => {
    render(<RetrievalResultCard index={0} result={{ title: "Član 1", score: 0.88, lexical_score: 0.4, semantic_score: 0.7 }} />);
    expect(screen.getByText(/Leksički: 0.400/i)).toBeInTheDocument();
    expect(screen.getByText(/Semantički: 0.700/i)).toBeInTheDocument();
  });

  it("submits finding review decisions", () => {
    const onDecision = vi.fn();
    render(<ReviewDecisionControls onDecision={onDecision} />);
    fireEvent.change(screen.getByLabelText(/Napomena recenzenta/i), { target: { value: "Provereno" } });
    fireEvent.click(screen.getByRole("button", { name: /Prihvati/i }));
    expect(onDecision).toHaveBeenCalledWith("accepted", "Provereno");
  });
});
