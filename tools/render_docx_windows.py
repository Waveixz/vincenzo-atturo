import runpy
import shutil
import sys
import tempfile
from pathlib import Path


SOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"
RENDERER = (
    "C:\\Users\\vatturo\\.codex\\plugins\\cache\\openai-primary-runtime\\documents\\"
    "26.905.11957\\skills\\documents\\render_docx.py"
)


original_which = shutil.which

TEMP_ROOT = Path(__file__).resolve().parents[1] / "tmp" / "render-docx-temp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(TEMP_ROOT)


def resolve_executable(command, mode=0, path=None):
    if command in {"soffice", "soffice.exe"}:
        return SOFFICE
    return original_which(command, mode=mode, path=path)


shutil.which = resolve_executable
sys.argv[0] = RENDERER
runpy.run_path(RENDERER, run_name="__main__")
