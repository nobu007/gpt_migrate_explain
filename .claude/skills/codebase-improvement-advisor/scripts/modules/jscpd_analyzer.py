"""JSCPD-based JavaScript/TypeScript duplication analysis."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

# jscpd availability check
JSCPD_AVAILABLE = False
try:
    result = subprocess.run(
        ["jscpd", "--version"], capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        JSCPD_AVAILABLE = True
except (subprocess.TimeoutExpired, FileNotFoundError):
    pass


@dataclass
class JSCPDConfig:
    """jscpd設定"""

    def __init__(self):
        self.js_ts_extensions = {".js", ".jsx", ".ts", ".tsx"}
        self.default_ignore_patterns = [
            "**/node_modules/**",
            "**/dist/**",
            "**/build/**",
            "**/coverage/**",
            "**/.git/**",
        ]
        self.threshold = 0
        self.timeout_seconds = 300


class JSCPDAnalyzer:
    """jscpd重複コード分析クラス"""

    def __init__(self, project_path: str, config: JSCPDConfig | None = None):
        self.project_path = Path(project_path).resolve()
        self.config = config or JSCPDConfig()

    def run_jscpd_analysis(self, files: list[Path]) -> list[dict]:
        """jscpdを実行して重複コードを検出"""
        if not JSCPD_AVAILABLE:
            return []

        js_ts_files = [f for f in files if f.suffix in self.config.js_ts_extensions]
        if not js_ts_files:
            return []

        try:
            cmd = [
                "jscpd",
                str(self.project_path),
                "--format",
                "json",
                "--output",
                "-",
                "--threshold",
                str(self.config.threshold),
            ]

            for pattern in self.config.default_ignore_patterns:
                cmd.extend(["--ignore", pattern])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=str(self.project_path),
            )

            if result.returncode != 0:
                print(f"jscpd failed: {result.stderr}")
                return []

            jscpd_result = json.loads(result.stdout)
            return self._parse_results(jscpd_result)

        except Exception as e:
            print(f"jscpd analysis failed: {e}")
            return []

    def _parse_results(self, jscpd_result: dict) -> list[dict]:
        """jscpd結果を解析"""
        duplications = []

        if not isinstance(jscpd_result, dict):
            return duplications

        dup_key = "duplication" if "duplication" in jscpd_result else "duplications"
        if dup_key not in jscpd_result:
            return duplications

        duplication_list = jscpd_result[dup_key]
        if not isinstance(duplication_list, list):
            return duplications

        for i, dup in enumerate(duplication_list):
            try:
                if not isinstance(dup, dict) or "fragments" not in dup:
                    continue

                fragments = dup["fragments"]
                if len(fragments) < 2:
                    continue

                first_fragment = fragments[0]
                for j, fragment in enumerate(fragments[1:], 1):
                    lines_count = fragment.get("size", 0)
                    severity = (
                        "high"
                        if lines_count >= 50
                        else "medium"
                        if lines_count >= 20
                        else "low"
                    )

                    duplication_info = {
                        "file_path": fragment.get("file", ""),
                        "line_number": max(1, fragment.get("start", 0) + 1),
                        "lines_count": lines_count,
                        "similarity": max(0.0, min(100.0, dup.get("similarity", 0))),
                        "first_occurrence": {
                            "file": first_fragment.get("file", "unknown"),
                            "line": max(1, first_fragment.get("start", 0) + 1),
                        },
                        "severity": severity,
                        "effort_estimate": {"high": "4h", "medium": "2h", "low": "1h"}[
                            severity
                        ],
                        "duplication_id": f"{i}_{j}",
                    }
                    duplications.append(duplication_info)

            except Exception as e:
                print(f"Error parsing duplication {i}: {e}")
                continue

        return duplications
