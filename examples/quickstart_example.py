#!/usr/bin/env python3
"""
Quickstart Example:
Demonstrates importing data, running Pearson correlation, creating an .omv project,
exporting a styled HTML report, and launching jamovi Desktop.
"""

import os
import sys

# Add mcp directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp"))
from jamovi_bridge import JamoviBridge

def main():
    bridge = JamoviBridge()
    if not bridge.is_available():
        print("jamovi Desktop or embedded engine not found. Please install jamovi.")
        sys.exit(1)

    print(f"Detected jamovi on {bridge.os_type}: {bridge.app_path}")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "student_grades.csv")
    output_omv = os.path.join(current_dir, "student_grades.omv")
    output_html = os.path.join(current_dir, "student_report.html")

    print("\n1. Running Pearson Correlation and generating .omv with embedded plots...")
    res = bridge.run_correlation(
        dataset_path=csv_path,
        vars_list=["study_hours", "exam_score"],
        pearson=True,
        sig=True,
        flag=True,
        output_omv_path=output_omv,
        include_plots=True
    )
    print(res["raw_output"])
    print(f"Generated .omv with embedded visualizations: {res.get('omv_path')}")

    print("3. Exporting standalone HTML report...")
    apa_writeup = (
        "A Pearson correlation coefficient was computed to assess the linear relationship between "
        "weekly study hours and exam performance. A statistically significant, strong positive correlation "
        "was observed, indicating that increased study duration is associated with higher test scores."
    )
    bridge.export_html_report(
        title="Student Grades Correlation Report",
        dataset_name="student_grades.csv",
        raw_output=res["raw_output"],
        apa_narrative=apa_writeup,
        output_html_path=output_html
    )
    print(f"Exported HTML report: {output_html}")

    print("\nTo launch in jamovi Desktop, run:")
    print(f"  bridge.open_project('{output_omv}')")

if __name__ == "__main__":
    main()
