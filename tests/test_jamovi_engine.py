"""
Tests for jamovi-antigravity bridge
"""

import os
import sys
import unittest
import tempfile
import csv

# Add mcp directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp"))
from jamovi_bridge import JamoviBridge


class TestJamoviBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = JamoviBridge()
        cls.test_dir = tempfile.mkdtemp(prefix="jamovi_test_")

        # Create sample csv
        cls.csv_path = os.path.join(cls.test_dir, "student_sample.csv")
        rows = [
            ["student_id", "group", "study_hours", "exam_score"],
            [1, "Online", 12.5, 78.0],
            [2, "Online", 14.0, 85.0],
            [3, "Online", 8.5, 62.0],
            [4, "Online", 16.0, 91.0],
            [5, "InPerson", 10.0, 70.0],
            [6, "InPerson", 15.5, 88.0],
            [7, "InPerson", 9.0, 65.0],
            [8, "InPerson", 18.0, 95.0]
        ]
        with open(cls.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def test_environment_detected(self):
        self.assertTrue(self.bridge.is_available(), f"jamovi engine not detected on {self.bridge.os_type}")
        self.assertIsNotNone(self.bridge.r_bin)

    def test_create_omv(self):
        omv_path = os.path.join(self.test_dir, "test_output.omv")
        res = self.bridge.create_omv_from_csv(
            csv_path=self.csv_path,
            output_omv_path=omv_path,
            col_types={"group": "Nominal", "study_hours": "Continuous", "exam_score": "Continuous"}
        )
        self.assertTrue(os.path.exists(res))
        self.assertGreater(os.path.getsize(res), 500)

    def test_pearson_correlation(self):
        res = self.bridge.run_correlation(
            dataset_path=self.csv_path,
            vars_list=["study_hours", "exam_score"],
            pearson=True
        )
        self.assertIn("Correlation Matrix", res["raw_output"])
        self.assertIn("study_hours", res["raw_output"])
        self.assertIn("exam_score", res["raw_output"])

    def test_independent_ttest(self):
        res = self.bridge.run_independent_ttest(
            dataset_path=self.csv_path,
            dep_vars=["exam_score"],
            group_var="group"
        )
        self.assertIn("Independent Samples T-Test", res["raw_output"])
        self.assertIn("exam_score", res["raw_output"])

    def test_anova(self):
        res = self.bridge.run_anova(
            dataset_path=self.csv_path,
            dep_var="exam_score",
            factors=["group"]
        )
        self.assertIn("ANOVA", res["raw_output"])
        self.assertIn("group", res["raw_output"])

    def test_regression(self):
        res = self.bridge.run_regression(
            dataset_path=self.csv_path,
            dep_var="exam_score",
            covs=["study_hours"]
        )
        self.assertIn("LINEAR REGRESSION", res["raw_output"])
        self.assertIn("Model Coefficients", res["raw_output"])

    def test_html_export(self):
        html_path = os.path.join(self.test_dir, "report.html")
        res = self.bridge.export_html_report(
            title="Student Performance Analysis",
            dataset_name="student_sample.csv",
            raw_output="Sample Raw Output",
            apa_narrative="There was a strong positive correlation, r(6) = .98, p < .001.",
            output_html_path=html_path
        )
        self.assertTrue(os.path.exists(res))
        with open(res, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Student Performance Analysis", content)
            self.assertIn("APA 7th Edition", content)

    def test_omv_embedded_correlation_analysis_and_plots(self):
        omv_path = os.path.join(self.test_dir, "test_corr_visualized.omv")
        res = self.bridge.run_correlation(
            dataset_path=self.csv_path,
            vars_list=["study_hours", "exam_score"],
            output_omv_path=omv_path,
            include_plots=True
        )
        self.assertIsNotNone(res.get("omv_path"))
        self.assertTrue(os.path.exists(omv_path))

        import zipfile
        with zipfile.ZipFile(omv_path, "r") as z:
            names = z.namelist()
            self.assertIn("01 empty/analysis", names)
            self.assertIn("02 corrMatrix/analysis", names)
            self.assertIn("03 empty/analysis", names)
            
            # Verify plot resource
            plot_entries = [n for n in names if n.startswith("02 corrMatrix/resources/") and n.endswith(".png")]
            self.assertGreater(len(plot_entries), 0)
            
            # Verify valid PNG signature
            png_bytes = z.read(plot_entries[0])
            self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(len(png_bytes), 5000)

    def test_omv_embedded_ttest_analysis_and_plots(self):
        omv_path = os.path.join(self.test_dir, "test_ttest_visualized.omv")
        res = self.bridge.run_independent_ttest(
            dataset_path=self.csv_path,
            dep_vars=["exam_score"],
            group_var="group",
            output_omv_path=omv_path,
            include_plots=True
        )
        self.assertIsNotNone(res.get("omv_path"))
        self.assertTrue(os.path.exists(omv_path))

        import zipfile
        with zipfile.ZipFile(omv_path, "r") as z:
            names = z.namelist()
            self.assertIn("01 empty/analysis", names)
            self.assertIn("02 ttestIS/analysis", names)
            self.assertIn("03 empty/analysis", names)
            
            plot_entries = [n for n in names if n.startswith("02 ttestIS/resources/") and n.endswith(".png")]
            self.assertGreater(len(plot_entries), 0)
            
            png_bytes = z.read(plot_entries[0])
            self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(len(png_bytes), 1000)


if __name__ == "__main__":
    unittest.main()
