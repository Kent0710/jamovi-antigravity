"""
jamovi Bridge: Platform detection, R/jmv engine execution, .omv generator,
HTML report exporter, and desktop app controller.
"""

import os
import sys
import subprocess
import json
import glob
import platform
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple, Any


class JamoviBridge:
    def __init__(self):
        self.os_type = platform.system()
        self.app_path = None
        self.r_home = None
        self.r_bin = None
        self.lib_paths = []
        self._detect_environment()

    def _detect_environment(self):
        if self.os_type == "Darwin":  # macOS
            possible_apps = [
                "/Applications/jamovi.app",
                os.path.expanduser("~/Applications/jamovi.app")
            ]
            for app in possible_apps:
                if os.path.isdir(app):
                    self.app_path = app
                    break

            if self.app_path:
                versions = glob.glob(f"{self.app_path}/Contents/Frameworks/R.framework/Versions/*")
                versions = [v for v in versions if os.path.basename(v) != "Current"]
                if versions:
                    # Prefer arm64 or latest version
                    versions.sort(reverse=True)
                    self.r_home = os.path.join(versions[0], "Resources")
                    self.r_bin = os.path.join(self.r_home, "bin", "R")

                modules_dir = os.path.join(self.app_path, "Contents", "Resources", "modules")
                if os.path.isdir(modules_dir):
                    self.lib_paths = [
                        os.path.join(modules_dir, "jmv", "R"),
                        os.path.join(modules_dir, "base", "R"),
                        modules_dir
                    ]

        elif self.os_type == "Windows":
            program_files = [os.environ.get("ProgramFiles", "C:\\Program Files")]
            found_dirs = []
            for pf in program_files:
                matches = glob.glob(os.path.join(pf, "jamovi*"))
                found_dirs.extend(matches)
            if found_dirs:
                self.app_path = sorted(found_dirs, reverse=True)[0]
                self.r_bin = os.path.join(self.app_path, "bin", "R.exe")
                self.r_home = self.app_path
                modules_dir = os.path.join(self.app_path, "modules")
                if os.path.isdir(modules_dir):
                    self.lib_paths = [
                        os.path.join(modules_dir, "jmv", "R"),
                        os.path.join(modules_dir, "base", "R"),
                        modules_dir
                    ]

        elif self.os_type == "Linux":
            candidates = ["/usr/lib/jamovi", "/opt/jamovi"]
            for cand in candidates:
                if os.path.isdir(cand):
                    self.app_path = cand
                    break
            if not self.app_path and shutil.which("flatpak"):
                res = subprocess.run(["flatpak", "info", "org.jamovi.jamovi"], capture_output=True, text=True)
                if res.returncode == 0:
                    self.app_path = "flatpak:org.jamovi.jamovi"

            if self.app_path and not self.app_path.startswith("flatpak"):
                self.r_bin = os.path.join(self.app_path, "bin", "R")
                self.r_home = self.app_path
                modules_dir = os.path.join(self.app_path, "modules")
                if os.path.isdir(modules_dir):
                    self.lib_paths = [
                        os.path.join(modules_dir, "jmv", "R"),
                        os.path.join(modules_dir, "base", "R"),
                        modules_dir
                    ]

    def is_available(self) -> bool:
        return bool(self.app_path and self.r_bin and os.path.exists(self.r_bin))

    def run_r(self, r_code: str, timeout: int = 60) -> Tuple[int, str, str]:
        if not self.is_available():
            raise RuntimeError(f"jamovi installation or embedded R engine not found on {self.os_type}.")

        lib_paths_r = ", ".join([f'"{p}"' for p in self.lib_paths])
        preamble = f"""
.libPaths(c({lib_paths_r}, .libPaths()))
suppressPackageStartupMessages(library(jmv))
suppressPackageStartupMessages(library(jmvReadWrite))
"""
        full_code = preamble + "\n" + r_code

        env = os.environ.copy()
        if self.r_home:
            env["R_HOME"] = self.r_home

        proc = subprocess.run(
            [self.r_bin, "--vanilla", "--slave", "-e", full_code],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return proc.returncode, proc.stdout, proc.stderr

    def create_omv_from_csv(self, csv_path: str, output_omv_path: str, col_types: Optional[Dict[str, str]] = None) -> str:
        """
        Converts a CSV or tabular file into a native .omv project file using jmvReadWrite.
        col_types: dict of variable_name -> "Nominal" | "Ordinal" | "Continuous" | "ID"
        """
        csv_path_abs = os.path.abspath(csv_path)
        output_omv_abs = os.path.abspath(output_omv_path)
        os.makedirs(os.path.dirname(output_omv_abs), exist_ok=True)

        type_transformations = []
        if col_types:
            for col, mtype in col_types.items():
                if mtype.lower() in ["nominal", "ordinal"]:
                    type_transformations.append(f'if ("{col}" %in% names(df)) df[["{col}"]] <- as.factor(df[["{col}"]])')
                elif mtype.lower() == "continuous":
                    type_transformations.append(f'if ("{col}" %in% names(df)) df[["{col}"]] <- as.numeric(as.character(df[["{col}"]]))')

        transform_code = "\n".join(type_transformations)

        r_code = f"""
df <- read.csv("{csv_path_abs}", stringsAsFactors = FALSE, check.names = FALSE)
{transform_code}
jmvReadWrite::write_omv(df, "{output_omv_abs}")
cat("OMV_CREATED_SUCCESS")
"""
        code, stdout, stderr = self.run_r(r_code)
        if code != 0 or "OMV_CREATED_SUCCESS" not in stdout:
            raise RuntimeError(f"Failed to create .omv file: {stderr or stdout}")
        return output_omv_abs

    def run_correlation(
        self,
        dataset_path: str,
        vars_list: List[str],
        pearson: bool = True,
        spearman: bool = False,
        sig: bool = True,
        flag: bool = True,
        ci: bool = True,
        hypothesis: str = "corr"
    ) -> Dict[str, Any]:
        """
        Runs jmv::corrMatrix and returns formatted tables and metrics.
        """
        dataset_path_abs = os.path.abspath(dataset_path)
        vars_r = ", ".join([f'"{v}"' for v in vars_list])

        r_code = f"""
if (endsWith(tolower("{dataset_path_abs}"), ".omv")) {{
    df <- jmvReadWrite::read_omv("{dataset_path_abs}")
}} else {{
    df <- read.csv("{dataset_path_abs}", stringsAsFactors = FALSE, check.names = FALSE)
}}

res <- jmv::corrMatrix(
    data = df,
    vars = c({vars_r}),
    pearson = {str(pearson).upper()},
    spearman = {str(spearman).upper()},
    sig = {str(sig).upper()},
    flag = {str(flag).upper()},
    ci = {str(ci).upper()},
    hypothesis = "{hypothesis}"
)

print(res)
"""
        code, stdout, stderr = self.run_r(r_code)
        if code != 0:
            raise RuntimeError(f"Error executing correlation: {stderr or stdout}")

        return {
            "raw_output": stdout,
            "variables": vars_list,
            "test": "Pearson Correlation" if pearson else "Spearman Correlation"
        }

    def run_independent_ttest(
        self,
        dataset_path: str,
        dep_vars: List[str],
        group_var: str,
        norm: bool = True,
        eqv: bool = True,
        effect_size: bool = True,
        ci: bool = True,
        welchs: bool = True
    ) -> Dict[str, Any]:
        dataset_path_abs = os.path.abspath(dataset_path)
        deps_r = ", ".join([f'"{v}"' for v in dep_vars])

        r_code = f"""
if (endsWith(tolower("{dataset_path_abs}"), ".omv")) {{
    df <- jmvReadWrite::read_omv("{dataset_path_abs}")
}} else {{
    df <- read.csv("{dataset_path_abs}", stringsAsFactors = FALSE, check.names = FALSE)
}}

df[["{group_var}"]] <- as.factor(df[["{group_var}"]])

res <- jmv::ttestIS(
    data = df,
    vars = c({deps_r}),
    group = "{group_var}",
    norm = {str(norm).upper()},
    eqv = {str(eqv).upper()},
    effectSize = {str(effect_size).upper()},
    ci = {str(ci).upper()},
    welchs = {str(welchs).upper()}
)

print(res)
"""
        code, stdout, stderr = self.run_r(r_code)
        if code != 0:
            raise RuntimeError(f"Error executing t-test: {stderr or stdout}")

        return {
            "raw_output": stdout,
            "dependent_variables": dep_vars,
            "grouping_variable": group_var,
            "test": "Independent Samples T-Test"
        }

    def run_descriptives(
        self,
        dataset_path: str,
        vars_list: List[str],
        split_by: Optional[str] = None
    ) -> Dict[str, Any]:
        dataset_path_abs = os.path.abspath(dataset_path)
        vars_r = ", ".join([f'"{v}"' for v in vars_list])
        split_param = f'splitBy = "{split_by}",' if split_by else ""

        r_code = f"""
if (endsWith(tolower("{dataset_path_abs}"), ".omv")) {{
    df <- jmvReadWrite::read_omv("{dataset_path_abs}")
}} else {{
    df <- read.csv("{dataset_path_abs}", stringsAsFactors = FALSE, check.names = FALSE)
}}

res <- jmv::descriptives(
    data = df,
    vars = c({vars_r}),
    {split_param}
    sd = TRUE,
    se = TRUE,
    skew = TRUE,
    kurt = TRUE,
    sw = TRUE
)

print(res)
"""
        code, stdout, stderr = self.run_r(r_code)
        if code != 0:
            raise RuntimeError(f"Error executing descriptives: {stderr or stdout}")

        return {
            "raw_output": stdout,
            "variables": vars_list,
            "split_by": split_by,
            "test": "Descriptives"
        }

    def run_paired_ttest(
        self,
        dataset_path: str,
        pairs: List[Tuple[str, str]],
        norm: bool = True,
        effect_size: bool = True,
        ci: bool = True
    ) -> Dict[str, Any]:
        dataset_path_abs = os.path.abspath(dataset_path)
        pairs_r_list = [f'list(i1="{p[0]}", i2="{p[1]}")' for p in pairs]
        pairs_r = ", ".join(pairs_r_list)

        r_code = f"""
if (endsWith(tolower("{dataset_path_abs}"), ".omv")) {{
    df <- jmvReadWrite::read_omv("{dataset_path_abs}")
}} else {{
    df <- read.csv("{dataset_path_abs}", stringsAsFactors = FALSE, check.names = FALSE)
}}

res <- jmv::ttestPS(
    data = df,
    pairs = list({pairs_r}),
    norm = {str(norm).upper()},
    effectSize = {str(effect_size).upper()},
    ci = {str(ci).upper()}
)

print(res)
"""
        code, stdout, stderr = self.run_r(r_code)
        if code != 0:
            raise RuntimeError(f"Error executing paired t-test: {stderr or stdout}")

        return {
            "raw_output": stdout,
            "pairs": pairs,
            "test": "Paired Samples T-Test"
        }

    def run_anova(
        self,
        dataset_path: str,
        dep_var: str,
        factors: List[str],
        post_hoc: bool = True,
        homo: bool = True,
        norm: bool = True
    ) -> Dict[str, Any]:
        dataset_path_abs = os.path.abspath(dataset_path)
        factors_r = ", ".join([f'"{f}"' for f in factors])
        post_hoc_r = f'postHoc = c({factors_r}),' if post_hoc else ""

        r_code = f"""
if (endsWith(tolower("{dataset_path_abs}"), ".omv")) {{
    df <- jmvReadWrite::read_omv("{dataset_path_abs}")
}} else {{
    df <- read.csv("{dataset_path_abs}", stringsAsFactors = FALSE, check.names = FALSE)
}}

for (f in c({factors_r})) {{
    df[[f]] <- as.factor(df[[f]])
}}

res <- jmv::ANOVA(
    data = df,
    dep = "{dep_var}",
    factors = c({factors_r}),
    effectSize = c("eta", "partEta"),
    homo = {str(homo).upper()},
    norm = {str(norm).upper()},
    {post_hoc_r}
    emMeans = list(c({factors_r}))
)

print(res)
"""
        code, stdout, stderr = self.run_r(r_code)
        if code != 0:
            raise RuntimeError(f"Error executing ANOVA: {stderr or stdout}")

        return {
            "raw_output": stdout,
            "dependent_variable": dep_var,
            "factors": factors,
            "test": "Standard ANOVA"
        }

    def run_regression(
        self,
        dataset_path: str,
        dep_var: str,
        covs: List[str],
        factors: Optional[List[str]] = None,
        collin: bool = True,
        durbin: bool = True
    ) -> Dict[str, Any]:
        dataset_path_abs = os.path.abspath(dataset_path)
        covs_r = ", ".join([f'"{c}"' for c in covs])
        factors_param = ""
        factors_prep = ""
        if factors:
            factors_r = ", ".join([f'"{f}"' for f in factors])
            factors_param = f'factors = c({factors_r}),'
            factors_prep = f'for (f in c({factors_r})) {{ df[[f]] <- as.factor(df[[f]]) }};'

        r_code = f"""
if (endsWith(tolower("{dataset_path_abs}"), ".omv")) {{
    df <- jmvReadWrite::read_omv("{dataset_path_abs}")
}} else {{
    df <- read.csv("{dataset_path_abs}", stringsAsFactors = FALSE, check.names = FALSE)
}}

{factors_prep}

res <- jmv::linReg(
    data = df,
    dep = "{dep_var}",
    covs = c({covs_r}),
    {factors_param}
    r2Adj = TRUE,
    stdEst = TRUE,
    ci = TRUE,
    collin = {str(collin).upper()},
    durbin = {str(durbin).upper()}
)

print(res)
"""
        code, stdout, stderr = self.run_r(r_code)
        if code != 0:
            raise RuntimeError(f"Error executing Linear Regression: {stderr or stdout}")

        return {
            "raw_output": stdout,
            "dependent_variable": dep_var,
            "covariates": covs,
            "test": "Linear Regression"
        }

    def run_contingency(
        self,
        dataset_path: str,
        row_var: str,
        col_var: str,
        counts_var: Optional[str] = None
    ) -> Dict[str, Any]:
        dataset_path_abs = os.path.abspath(dataset_path)
        counts_param = f'counts = "{counts_var}",' if counts_var else ""

        r_code = f"""
if (endsWith(tolower("{dataset_path_abs}"), ".omv")) {{
    df <- jmvReadWrite::read_omv("{dataset_path_abs}")
}} else {{
    df <- read.csv("{dataset_path_abs}", stringsAsFactors = FALSE, check.names = FALSE)
}}

res <- jmv::contingency(
    data = df,
    row = "{row_var}",
    col = "{col_var}",
    {counts_param}
    chiSq = TRUE,
    phiCra = TRUE,
    expected = TRUE
)

print(res)
"""
        code, stdout, stderr = self.run_r(r_code)
        if code != 0:
            raise RuntimeError(f"Error executing Contingency Tables: {stderr or stdout}")

        return {
            "raw_output": stdout,
            "row_variable": row_var,
            "col_variable": col_var,
            "test": "Contingency Tables (Chi-Square)"
        }

    def export_html_report(self, title: str, dataset_name: str, raw_output: str, apa_narrative: str, output_html_path: str) -> str:
        """
        Creates a clean, styled standalone HTML report of the jamovi results.
        """
        output_abs = os.path.abspath(output_html_path)
        os.makedirs(os.path.dirname(output_abs), exist_ok=True)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f7f9fa;
            color: #212529;
            line-height: 1.6;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            padding: 36px;
        }}
        .header {{
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        h1 {{
            color: #2c3e50;
            font-size: 26px;
            margin: 0 0 8px 0;
        }}
        .meta {{
            font-size: 14px;
            color: #6c757d;
        }}
        h2 {{
            color: #34495e;
            font-size: 20px;
            margin-top: 28px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        pre.jamovi-output {{
            background: #2b303c;
            color: #f8f9fa;
            padding: 18px;
            border-radius: 6px;
            font-family: "SF Mono", "Consolas", "Courier New", monospace;
            font-size: 13px;
            overflow-x: auto;
            line-height: 1.5;
        }}
        .apa-card {{
            background: #eef7ff;
            border-left: 4px solid #0070e0;
            padding: 16px 20px;
            border-radius: 4px;
            font-size: 15px;
            margin-top: 16px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #e9ecef;
            font-size: 12px;
            color: #868e96;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                <span>Dataset: <strong>{dataset_name}</strong></span> |
                <span>Engine: <strong>jamovi official jmv / R</strong></span>
            </div>
        </div>

        <h2>Official jamovi Results</h2>
        <pre class="jamovi-output">{raw_output}</pre>

        <h2>APA 7th Edition Write-Up & Interpretation</h2>
        <div class="apa-card">
            {apa_narrative.replace(chr(10), '<br>')}
        </div>

        <div class="footer">
            Generated automatically via jamovi-antigravity bridge for jamovi Desktop.
        </div>
    </div>
</body>
</html>
"""
        with open(output_abs, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_abs

    def open_project(self, project_path: str) -> bool:
        project_abs = os.path.abspath(project_path)
        if not os.path.exists(project_abs):
            raise FileNotFoundError(f"Project file not found: {project_abs}")

        if self.os_type == "Darwin":
            res = subprocess.run(["open", "-a", "/Applications/jamovi.app", project_abs])
            return res.returncode == 0
        elif self.os_type == "Windows":
            os.startfile(project_abs)
            return True
        elif self.os_type == "Linux":
            res = subprocess.run(["xdg-open", project_abs])
            return res.returncode == 0
        return False

    def capture_active_window(self, output_image_path: str) -> Optional[str]:
        output_abs = os.path.abspath(output_image_path)
        os.makedirs(os.path.dirname(output_abs), exist_ok=True)

        if self.os_type == "Darwin":
            # Find jamovi window id or take display capture
            res = subprocess.run(["screencapture", "-x", output_abs])
            if res.returncode == 0 and os.path.exists(output_abs):
                return output_abs
        return None
