# jamovi MCP Server Instructions

This MCP server connects Antigravity directly to the local jamovi installation on this machine.

## Available Tools

1. `jamovi_run_analysis`:
   - Runs statistical analyses (`correlation`, `ttest_is`, `ttest_ps`, `anova`, `regression`, `descriptives`, `contingency`).
   - Automatically executes via jamovi's official R engine.
   - Can generate `.omv` project files and `.html` reports in one call.
   - Can optionally open the project in jamovi Desktop immediately.

2. `jamovi_create_omv`:
   - Converts tabular datasets (`.csv`, `.xlsx`) into native `.omv` jamovi project files.

3. `jamovi_export_report`:
   - Generates standalone, styled `.html` reports with authentic jamovi ASCII tables and APA 7th Edition write-ups.

4. `jamovi_open_project`:
   - Launches jamovi Desktop (`/Applications/jamovi.app`) to display the `.omv` file live on screen.

5. `jamovi_capture_window`:
   - Captures the active window as screenshot proof for professors.
