# jamovi-antigravity

Model Context Protocol (MCP) server and agent integration connecting Google Antigravity to jamovi Desktop.

jamovi-antigravity automates statistical workflows by bridging AI coding agents directly to the official jamovi statistical engine (`jmv`). It enables hands-free dataset ingestion, rigorous hypothesis testing, APA 7th Edition reporting, native `.omv` project file generation, and live desktop application launching.

---

## Key Capabilities

* Direct Execution: Runs statistical tests directly through the official jamovi R engine (`jmv`) bundled inside your desktop application.
* Native Project Generation: Automatically compiles tabular datasets and variable attributes into native `.omv` project files ready for professor submission.
* Easily Downloadable Reports: Exports self-contained HTML reports featuring official jamovi ASCII tables, charts, and APA 7th Edition narrative interpretations.
* Desktop App Launching: Directly launches the jamovi Desktop application with the generated project loaded on screen.
* Zero External Dependencies: Built entirely on Python 3 standard libraries and the local jamovi installation.

---

## One-Click Installation

### macOS and Linux

Run the following command in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/Kent0710/jamovi-antigravity/main/install.sh | bash
```

### Windows (PowerShell)

Run the following command in PowerShell:

```powershell
irm https://raw.githubusercontent.com/Kent0710/jamovi-antigravity/main/install.ps1 | iex
```

### Manual Installation (From Git)

```bash
git clone https://github.com/Kent0710/jamovi-antigravity.git
cd jamovi-antigravity
chmod +x install.sh
./install.sh
```

---

## What the Installer Does

1. Detects jamovi: Locates the local jamovi installation path:
   * macOS: `/Applications/jamovi.app`
   * Windows: `C:\Program Files\jamovi *`
   * Linux: `/usr/lib/jamovi`, `/opt/jamovi`, or Flatpak
2. Validates Statistical Engine: Verifies the bundled Python and R runtimes alongside `jmv`, `jmvcore`, and `jmvReadWrite` packages.
3. Installs MCP Server: Deploys the MCP server and tool definitions into `~/.gemini/antigravity/mcp/jamovi/`.
4. Installs Agent: Installs the `jamovi-analyst` subagent definition into `~/.gemini/config/agents/jamovi-analyst.md`.
5. Runs Smoke Test: Executes an automated smoke test to verify engine accessibility.

---

## How to Use with Antigravity

Once installed, open Antigravity and converse with the statistical agent:

```text
@jamovi-analyst Here is my dataset student_grades.csv. Run a Pearson correlation between study_hours and exam_score, test normality, and generate an APA 7th report.
```

The agent will:
1. Load and inspect the dataset.
2. Execute `jmv::corrMatrix` with hypothesis testing and normality checks.
3. Output the official jamovi ASCII results table.
4. Provide the full APA 7th Edition interpretation.
5. Generate clickable download links:
   * Download Project (.omv): Native project openable in jamovi Desktop.
   * Download Formatted Report (.html): Standalone HTML document.
6. Launch jamovi Desktop (`open -a /Applications/jamovi.app <file.omv>`) so you can inspect the results immediately.

---

## Supported Statistical Tests

| Statistical Procedure | jamovi Engine Function | Key Options |
| :--- | :--- | :--- |
| Descriptives | jmv::descriptives | Mean, Median, SD, SE, Skewness, Kurtosis, Shapiro-Wilk |
| Pearson Correlation | jmv::corrMatrix | Pearson r, p-values, 95% Confidence Intervals, Hypothesis flag |
| Spearman Correlation | jmv::corrMatrix | Spearman rho, non-parametric rank correlation |
| Independent Samples T-Test | jmv::ttestIS | Student t, Welch t, Levene test, Cohen d effect size |
| Paired Samples T-Test | jmv::ttestPS | Student t, Wilcoxon W, Normality checks |
| One-Way ANOVA | jmv::anovaOneW | Fisher F, Welch F, Homogeneity test, Tukey post-hoc |
| Factorial ANOVA | jmv::ANOVA | Eta-squared, Partial eta-squared, Estimated marginal means |
| Linear Regression | jmv::linReg | Model fit, R-squared, VIF collinearity, Durbin-Watson |
| Contingency Tables | jmv::contingency | Pearson Chi-square, Cramer V, Expected frequencies |

---

## Repository Structure

```text
jamovi-antigravity/
|-- README.md               # Documentation
|-- LICENSE                 # MIT License
|-- install.sh              # One-click installer for macOS and Linux
|-- install.ps1             # One-click installer for Windows
|-- agent/
|   `-- jamovi-analyst.md   # Antigravity agent definition
|-- mcp/
|   |-- server.py           # JSON-RPC MCP server
|   |-- jamovi_bridge.py    # Platform detection and R/jmv execution bridge
|   |-- requirements.txt    # Dependency notes (standard library only)
|   |-- instructions.md     # Agent instructions
|   `-- tools/              # MCP tool schemas
|       |-- jamovi_run_analysis.json
|       |-- jamovi_create_omv.json
|       |-- jamovi_export_report.json
|       |-- jamovi_open_project.json
|       `-- jamovi_capture_window.json
|-- examples/
|   |-- student_grades.csv  # Sample dataset
|   `-- quickstart_example.py # Standalone Python demo script
`-- tests/
    `-- test_jamovi_engine.py # Test suite
```

---

## Testing

Run the test suite to verify the statistical engine and file generation:

```bash
python3 tests/test_jamovi_engine.py
```

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
