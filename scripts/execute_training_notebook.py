from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def build_notebook(duckdb_path: Path) -> nbformat.NotebookNode:
    notebook = nbformat.v4.new_notebook()
    notebook.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    }
    notebook.cells = [
        nbformat.v4.new_markdown_cell(
            "# NASA C-MAPSS Final Training\n\n"
            "This notebook is executed by `nbclient`. The code cell below launches the complete "
            "dbt-backed training, evaluation, artifact logging, and MLflow Registry workflow."
        ),
        nbformat.v4.new_code_cell(
            "import subprocess\n"
            "import sys\n\n"
            "command = [\n"
            "    sys.executable, 'scripts/train_model.py',\n"
            "    '--source', 'duckdb',\n"
            f"    '--duckdb-path', {str(duckdb_path)!r},\n"
            "]\n"
            "subprocess.run(command, check=True)"
        ),
        nbformat.v4.new_code_cell(
            "import json\n"
            "import os\n"
            "from pathlib import Path\n\n"
            "metrics = json.loads(Path('reports/model_metrics/final_evaluation.json').read_text())\n"
            "expected_subsets = os.getenv('TRAIN_SUBSETS', 'FD001 FD002 FD003 FD004').split()\n"
            "assert metrics['subsets'] == expected_subsets\n"
            "assert metrics['dataset']['pipeline_source'] == 'duckdb'\n"
            "assert metrics['mlflow']['registered_model_version']\n"
            "{\n"
            "    'train_rows': metrics['train_rows'],\n"
            "    'test_engines': metrics['final_test_engines'],\n"
            "    'final_metrics': metrics['models']['final_gradient_boosting']['standard_final_cycle_metrics'],\n"
            "    'registered_model': metrics['mlflow']['model_uri'],\n"
            "}"
        ),
    ]
    return notebook


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute and preserve the final training notebook.")
    parser.add_argument("--duckdb-path", type=Path, default=Path("cmapss_ingestion.duckdb"))
    parser.add_argument("--source-path", type=Path, default=Path("notebooks/training_pipeline.ipynb"))
    parser.add_argument("--output-path", type=Path, default=Path("notebooks/training_executed.ipynb"))
    args = parser.parse_args()

    notebook = build_notebook(args.duckdb_path)
    args.source_path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, args.source_path)
    with tempfile.TemporaryDirectory(prefix="industrial-health-kernel-") as temp_dir:
        kernel_dir = Path(temp_dir) / "python3"
        kernel_dir.mkdir()
        (kernel_dir / "kernel.json").write_text(
            json.dumps(
                {
                    "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                    "display_name": "Industrial Health Python",
                    "language": "python",
                }
            ),
            encoding="utf-8",
        )
        spec_manager = KernelSpecManager(kernel_dirs=[temp_dir])
        kernel_manager = KernelManager(kernel_name="python3", kernel_spec_manager=spec_manager)
        executed = NotebookClient(
            notebook,
            km=kernel_manager,
            timeout=7200,
            startup_timeout=300,
            resources={"metadata": {"path": str(Path.cwd())}},
        ).execute()
    nbformat.write(executed, args.output_path)
    print(f"executed training notebook: {args.output_path}")


if __name__ == "__main__":
    main()
