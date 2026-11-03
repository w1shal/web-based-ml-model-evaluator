# Sprint 2 demo video: 2 minutes, working product

Record the merged `main` branch, after every PR is merged. Seed the demo data first: `python backend/scripts/seed_history.py`.

| Time | Show | Say |
|---|---|---|
| 0:00 to 0:10 | App home | Name of the project and the four-step flow |
| 0:10 to 0:25 | Register, then log in | Validation errors, JWT login |
| 0:25 to 0:55 | Upload a CSV, configure, pick 3 algorithms, evaluate | Metrics table, comparison chart, confusion matrix, sorted ranking (M2, M3, M4 parts) |
| 0:55 to 1:10 | Export PDF and CSV | Values match the screen |
| 1:10 to 1:30 | History page: new run appears, open it, delete it | Per-user history, owner-only delete |
| 1:30 to 1:45 | Guest run, then check history does not list it | Guests are not saved |
| 1:45 to 2:00 | Terminal: repeat bad logins until 429; `curl -I http://localhost/` shows the 301; show CI green and the RTM | Rate limiting, HTTPS, tests and traceability |

Upload the video to `demo/sprint2_demo.mp4` (compress it if it is near GitHub's 100 MB limit). Then freeze development: no merges after the video.
