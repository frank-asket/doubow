# Job search pipeline — Doubow figures

| File | Purpose |
| --- | --- |
| **`pipeline-stages.png`** | Five default stages (use this in README / slides; raster for reliable rendering). |
| **`scoring-and-feedback-loop.png`** | Catalog + profile → blend → Discover; feedback loop. |

**Sources:** matching **`*.svg`** files (edit in Illustrator/Figma or regenerate). Regenerate PNG after SVG edits:

```bash
cd docs/architecture/job-search-pipeline
rsvg-convert -w 1800 pipeline-stages.svg -o pipeline-stages.png
rsvg-convert -w 1800 scoring-and-feedback-loop.svg -o scoring-and-feedback-loop.png
```

Diagrams mirror `JobSearchPipelineCoordinator` and scoring in `backend/api_gateway/services/job_search_pipeline.py` and `services/jobs_service.py`.
