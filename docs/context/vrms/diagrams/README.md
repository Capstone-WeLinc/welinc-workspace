# VRMS paper diagrams

One file per diagram, named by its paper section. Each has its source plus a PNG export (export an SVG from the source when you need one). Facts come from the code (see `docs/_private/vrms/diagram-facts.md`); black on white with WeLinc gold as the only accent.

| Section | Diagram | Source |
|---|---|---|
| 4.2.1 | System context | `4.2.1-context.drawio` |
| 4.3.1, 4.3.2 | BPMN as is and to be | `4.3.1-bpmn-as-is.drawio`, `4.3.2-bpmn-to-be.drawio` |
| 4.4.1 | Component | `4.4.1-component.puml` |
| 4.4.2 | Use case, three sequences, class | `4.4.2-*.puml` |
| 4.5.1 | ERD (business tables) | `4.5.1-erd.puml` (generated) |
| 4.5.2 | Physical schema (every table) | `4.5.2-physical-schema.puml` (generated) |
| 4.5.4 | DFD level 0 and 1 | `4.5.4-dfd-level-0.drawio`, `4.5.4-dfd-level-1.drawio` |
| 4.6.2 to 4.6.4 | Deployment, network and security, cloud | `4.6.*.drawio` |

To rebuild (you may run any of these from this folder):

```bash
node generate-erd.mjs                      # after a schema.prisma change: rewrites the 4.5.x sources
docker run --rm -v "$PWD":/data -w /data plantuml/plantuml -tpng *.puml          # add -tsvg for an SVG
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -s 2 -o 4.2.1-context.png 4.2.1-context.drawio
```

The `.drawio` files open in draw.io desktop for hand edits; `_style.iuml` holds the shared PlantUML look.
