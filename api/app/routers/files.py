from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..security import require_api_key
from ..settings import settings

router = APIRouter(tags=["files"], dependencies=[Depends(require_api_key)])

# _ROOT — абсолютный путь к папке с результатами ComfyUI внутри контейнера.
_ROOT = Path(settings.comfy_output_dir).resolve()


@router.get("/files/{filename}")
def get_file(filename: str):
    """Отдать файл изображения по имени."""
    if (
        "/" in filename
        or "\\" in filename
        or ".." in filename
        or filename.startswith(".")
    ):
        raise HTTPException(status_code=400, detail="bad filename")

    path = (_ROOT / filename).resolve()

    # Двойная страховка: финальный путь должен лежать внутри _ROOT.
    if _ROOT not in path.parents and path != _ROOT:
        raise HTTPException(status_code=400, detail="bad path")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="file not found")

    return FileResponse(path, media_type="image/png", filename=filename)
