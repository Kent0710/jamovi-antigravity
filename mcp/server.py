#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server for jamovi.
Bridges Antigravity and any MCP-compliant LLM client directly to the jamovi engine.
"""

import os
import sys
import json
import logging
from typing import Any, Dict, List

# Ensure bridge is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from jamovi_bridge import JamoviBridge

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[jamovi-mcp] %(levelname)s: %(message)s")
logger = logging.getLogger("jamovi-mcp")

bridge = JamoviBridge()

TOOLS = [
    {
        "name": "jamovi_run_analysis",
        "description": "Execute statistical analyses (correlation, t-test, ANOVA, linear regression, descriptives, contingency) using jamovi's official statistical engine. Returns official ASCII tables, APA 7th Edition writeup, and can automatically generate a native .omv project file and standalone HTML report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "test_type": {
                    "type": "string",
                    "enum": ["correlation", "ttest_is", "ttest_ps", "anova", "regression", "descriptives", "contingency"],
                    "description": "Type of statistical analysis to perform."
                },
                "dataset_path": {
                    "type": "string",
                    "description": "Path to the dataset (.csv, .xlsx, or .omv)."
                },
                "variables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Variables to analyze (e.g. ['study_hours', 'exam_score'])."
                },
                "group_var": {
                    "type": "string",
                    "description": "Grouping/independent variable for t-test or ANOVA."
                },
                "output_omv_path": {
                    "type": "string",
                    "description": "Optional file path to save the native .omv jamovi project."
                },
                "output_html_path": {
                    "type": "string",
                    "description": "Optional file path to save a standalone HTML report."
                },
                "include_plots": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to automatically generate and embed high-resolution visual plots into the .omv project canvas."
                },
                "open_in_jamovi": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to immediately launch the desktop app with the generated project."
                }
            },
            "required": ["test_type", "dataset_path", "variables"]
        }
    },
    {
        "name": "jamovi_create_omv",
        "description": "Convert a CSV or Excel dataset into a native jamovi (.omv) project file with custom column metadata (measurement levels, factor labels). Optionally embed initial analyses and visualizations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "csv_path": {
                    "type": "string",
                    "description": "Path to input CSV file."
                },
                "output_omv_path": {
                    "type": "string",
                    "description": "Destination path for the generated .omv file."
                },
                "column_types": {
                    "type": "object",
                    "description": "Optional mapping of column name to measurement scale: 'Nominal', 'Ordinal', or 'Continuous'."
                },
                "test_type": {
                    "type": "string",
                    "description": "Optional initial analysis to embed: 'correlation', 'ttest_is', 'anova', etc."
                },
                "variables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional variables for embedded initial analysis."
                },
                "group_var": {
                    "type": "string",
                    "description": "Optional grouping variable for embedded initial analysis."
                },
                "include_plots": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include pre-rendered visual plots."
                }
            },
            "required": ["csv_path", "output_omv_path"]
        }
    },
    {
        "name": "jamovi_open_project",
        "description": "Open a .omv project or supported dataset in the jamovi Desktop application on screen.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to the .omv file to open."
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "jamovi_export_report",
        "description": "Generate a standalone, publication-ready HTML report with formatted jamovi tables and APA 7th Edition narrative interpretation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the report."
                },
                "dataset_name": {
                    "type": "string",
                    "description": "Name or identifier of the analyzed dataset."
                },
                "raw_output": {
                    "type": "string",
                    "description": "The ASCII output table returned by the jamovi engine."
                },
                "apa_narrative": {
                    "type": "string",
                    "description": "The APA 7th Edition narrative interpretation."
                },
                "output_html_path": {
                    "type": "string",
                    "description": "Destination file path for the .html report."
                }
            },
            "required": ["title", "dataset_name", "raw_output", "apa_narrative", "output_html_path"]
        }
    },
    {
        "name": "jamovi_capture_window",
        "description": "Capture a screenshot of the active jamovi Desktop window as visual verification for academic submissions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output_image_path": {
                    "type": "string",
                    "description": "Destination file path for the screenshot image (.png)."
                }
            },
            "required": ["output_image_path"]
        }
    }
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if name == "jamovi_run_analysis":
            test_type = arguments.get("test_type")
            dataset_path = arguments.get("dataset_path")
            variables = arguments.get("variables", [])
            group_var = arguments.get("group_var")
            output_omv = arguments.get("output_omv_path")
            output_html = arguments.get("output_html_path")
            include_plots = arguments.get("include_plots", True)
            open_jamovi = arguments.get("open_in_jamovi", False)

            if test_type == "correlation":
                res = bridge.run_correlation(dataset_path, variables, output_omv_path=output_omv, include_plots=include_plots)
            elif test_type == "ttest_is":
                if not group_var:
                    raise ValueError("group_var is required for independent samples t-test")
                res = bridge.run_independent_ttest(dataset_path, variables, group_var, output_omv_path=output_omv, include_plots=include_plots)
            elif test_type == "ttest_ps":
                pairs = [(variables[i], variables[i + 1]) for i in range(0, len(variables) - 1, 2)]
                res = bridge.run_paired_ttest(dataset_path, pairs, output_omv_path=output_omv, include_plots=include_plots)
            elif test_type == "anova":
                if not group_var:
                    raise ValueError("group_var (factor) is required for ANOVA")
                res = bridge.run_anova(dataset_path, variables[0], [group_var], output_omv_path=output_omv, include_plots=include_plots)
            elif test_type == "regression":
                res = bridge.run_regression(dataset_path, variables[0], variables[1:], output_omv_path=output_omv, include_plots=include_plots)
            elif test_type == "descriptives":
                res = bridge.run_descriptives(dataset_path, variables, split_by=group_var, output_omv_path=output_omv, include_plots=include_plots)
            elif test_type in ["contingency", "contTables"]:
                if len(variables) < 2:
                    raise ValueError("At least 2 variables (row and column) are required for contingency analysis")
                res = bridge.run_contingency(dataset_path, variables[0], variables[1], output_omv_path=output_omv, include_plots=include_plots)
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            omv_created = res.get("omv_path")
            if not omv_created and output_omv:
                omv_created = bridge.create_omv_from_csv(dataset_path, output_omv)

            html_created = None
            if output_html:
                html_created = bridge.export_html_report(
                    title=f"jamovi Analysis: {res.get('test', test_type)}",
                    dataset_name=os.path.basename(dataset_path),
                    raw_output=res.get("raw_output", ""),
                    apa_narrative="Statistical analysis completed via official jamovi engine.",
                    output_html_path=output_html
                )

            if open_jamovi and (omv_created or dataset_path.endswith(".omv")):
                target = omv_created or dataset_path
                bridge.open_project(target)

            output_text = f"=== JAMOVI OFFICIAL OUTPUT ===\n{res.get('raw_output')}\n"
            if omv_created:
                output_text += f"\nNative jamovi project created with embedded results & plots: {omv_created}\n"
            if html_created:
                output_text += f"HTML report created: {html_created}\n"

            return {"content": [{"type": "text", "text": output_text}]}

        elif name == "jamovi_create_omv":
            csv_path = arguments["csv_path"]
            output_omv_path = arguments["output_omv_path"]
            col_types = arguments.get("column_types")
            test_type = arguments.get("test_type")
            
            if test_type:
                variables = arguments.get("variables", [])
                group_var = arguments.get("group_var")
                include_plots = arguments.get("include_plots", True)
                result_path = bridge.create_omv_with_analysis(
                    dataset_path=csv_path,
                    output_omv_path=output_omv_path,
                    test_type=test_type,
                    variables=variables,
                    group_var=group_var,
                    col_types=col_types,
                    include_plots=include_plots
                )
            else:
                result_path = bridge.create_omv_from_csv(csv_path, output_omv_path, col_types)
                
            return {"content": [{"type": "text", "text": f"Successfully created jamovi project at: {result_path}"}]}

        elif name == "jamovi_open_project":
            project_path = arguments["project_path"]
            success = bridge.open_project(project_path)
            return {"content": [{"type": "text", "text": f"Launched jamovi desktop: {success}"}]}

        elif name == "jamovi_export_report":
            res_path = bridge.export_html_report(
                title=arguments["title"],
                dataset_name=arguments["dataset_name"],
                raw_output=arguments["raw_output"],
                apa_narrative=arguments["apa_narrative"],
                output_html_path=arguments["output_html_path"]
            )
            return {"content": [{"type": "text", "text": f"Successfully exported HTML report to: {res_path}"}]}

        elif name == "jamovi_capture_window":
            output_img = arguments["output_image_path"]
            captured = bridge.capture_active_window(output_img)
            if captured:
                return {"content": [{"type": "text", "text": f"Screenshot saved to: {captured}"}]}
            return {"content": [{"type": "text", "text": "Screenshot capture failed or unsupported on this platform."}], "isError": True}

        else:
            return {"content": [{"type": "text", "text": f"Tool '{name}' not found."}], "isError": True}

    except Exception as e:
        logger.exception("Error during tool call")
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}


def main():
    logger.info("Starting jamovi-mcp server...")
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_id = req.get("id")
        method = req.get("method")

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "jamovi-mcp", "version": "1.0.0"}
                }
            }
        elif method == "notifications/initialized":
            continue
        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            result = handle_tool_call(name, args)
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": result}
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
