import json
import re
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "modules.json"


def _slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "modulo"


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {"version": 2, "modules": []}
    with REGISTRY_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    data.setdefault("version", 2)
    data.setdefault("modules", [])
    return data


def save_registry(data: dict) -> None:
    temp = REGISTRY_PATH.with_suffix(".json.tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    temp.replace(REGISTRY_PATH)


def all_modules() -> list[dict]:
    return sorted(load_registry()["modules"], key=lambda m: (m.get("order", 9999), m.get("name", "")))


def enabled_modules() -> list[dict]:
    return [module for module in all_modules() if module.get("enabled", True)]


def get_module(module_id: str):
    return next((module for module in all_modules() if module.get("id") == module_id), None)


def add_module(name, icon="MOD", description="", features=None, enabled=True,
               open_mode="internal", allow_new_tab=True, url="", entrypoint=""):
    data = load_registry()
    used_ids = {module.get("id") for module in data["modules"]}
    module_id = _slug(name)
    base = module_id
    counter = 2
    while module_id in used_ids:
        module_id = f"{base}_{counter}"
        counter += 1

    max_order = max((module.get("order", 0) for module in data["modules"]), default=0)
    if open_mode == "internal" and not entrypoint:
        entrypoint = f"modules.{module_id}.module"

    module = {
        "id": module_id,
        "name": name.strip(),
        "icon": (icon or "MOD").strip(),
        "description": description.strip(),
        "features": features or [],
        "enabled": bool(enabled),
        "order": max_order + 10,
        "open_mode": open_mode,
        "allow_new_tab": bool(allow_new_tab),
        "url": url.strip(),
        "entrypoint": entrypoint.strip(),
        "system": False,
    }
    data["modules"].append(module)
    save_registry(data)
    return module


def update_module(module_id: str, **changes):
    data = load_registry()
    for module in data["modules"]:
        if module.get("id") == module_id:
            module.update(changes)
            save_registry(data)
            return module
    raise KeyError(module_id)


def delete_module(module_id: str) -> None:
    data = load_registry()
    before = len(data["modules"])
    data["modules"] = [module for module in data["modules"] if module.get("id") != module_id]
    if len(data["modules"]) == before:
        raise KeyError(module_id)
    save_registry(data)
