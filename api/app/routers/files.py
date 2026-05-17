# GET /files/{filename}

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..settings import settings

router = APIRouter(tags=["files"])

# _ROOT — абсолютный путь к папке с результатами ComfyUI внутри контейнера.
# resolve() — превращает в абсолютный путь без ".." и симлинков.
_ROOT = Path(settings.comfy_output_dir).resolve()


@router.get("/files/{filename}")
def get_file(filename: str):
    """
    Отдать файл изображения по имени.

    Клиент получает имя файла из GET /jobs/{id}/result → поле filename,
    затем запрашивает GET /files/{filename} — и получает PNG.
    """
    # Защита от path traversal: запрещаем сепараторы и '..' в имени.

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
