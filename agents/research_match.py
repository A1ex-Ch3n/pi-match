import json
import os
import anthropic


def score_research_fit(
    student_background: str,
    pi_abstracts: list[str],
    pi_research_areas: list[str],
    pi_paper_titles: list[str] | None = None,
) -> tuple[float, str]:
    areas_text = ", ".join(pi_research_areas) if pi_research_areas else "not specified"

    if pi_abstracts:
        pi_context = "PI Recent Abstracts:\n" + "\n\n".join(
            f"Abstract {i+1}: {a}" for i, a in enumerate(pi_abstracts)
        )
        cite_instruction = "Write a rationale of 2–3 sentences that MUST cite specific paper topics or methods from the abstracts above."
    elif pi_paper_titles:
        titles_text = "\n".join(f"- {t}" for t in pi_paper_titles[:10])
        pi_context = f"PI Recent Paper Titles (no full abstracts available):\n{titles_text}"
        cite_instruction = "Write a rationale of 2–3 sentences citing specific paper titles or research areas above."
    else:
        pi_context = "No abstracts or paper titles available. Use the research areas listed above."
        cite_instruction = "Write a rationale of 2–3 sentences based on the PI's research areas."

    prompt = f"""You are evaluating research fit between a PhD applicant and a PI.

PI Research Areas: {areas_text}

{pi_context}

Student Background:
{student_background}

Score the research fit from 0 to 100 where:
- 0–30: Little to no overlap
- 31–60: Some thematic overlap but different methods or focus
- 61–80: Clear overlap in research direction or methods
- 81–100: Strong alignment in both topic and approach

{cite_instruction} Do not use generic phrases like "strong overlap" without citing specifics.

Respond ONLY with valid JSON: {{"score": float, "rationale": str}}"""

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return 50.0, "Unable to compute research fit score; defaulting to neutral."
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        score = float(data["score"])
        rationale = str(data["rationale"])
        return score, rationale
    except (json.JSONDecodeError, KeyError, ValueError):
        return 50.0, "Unable to compute research fit score; defaulting to neutral."
    except Exception:
        return 50.0, "Unable to compute research fit score; defaulting to neutral."


if __name__ == "__main__":
    student_bg = (
        "I have two years of experience applying deep learning to genomics, "
        "specifically using transformer architectures for protein sequence classification "
        "and single-cell RNA-seq analysis. I am familiar with PyTorch and have contributed "
        "to a paper on contrastive learning for multi-omics data integration."
    )
    pi_abstracts = [
        "We present a graph neural network approach to predicting protein–protein "
        "interaction networks from amino acid sequences, achieving state-of-the-art "
        "performance on the STRING benchmark.",
        "This work introduces a self-supervised pre-training strategy for single-cell "
        "transcriptomics that learns cell-type embeddings without labeled data, enabling "
        "transfer across tissues and species.",
    ]
    pi_areas = ["computational biology", "protein structure", "single-cell genomics"]

    score, rationale = score_research_fit(student_bg, pi_abstracts, pi_areas)
    print(f"Score: {score}")
    print(f"Rationale: {rationale}")
