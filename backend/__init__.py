"""Blender — Store desktop plugin (direct TCP to Blender MCP addon)."""

from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .connection import DEFAULT_HOST, DEFAULT_PORT, BlenderConnection
from .deploy_addon import deploy_addon

log = logging.getLogger("uefn.plugin.blender")
PLUGIN_ID = "blender"

_conn: BlenderConnection | None = None


def _prefs() -> dict[str, Any]:
    try:
        from frontend.ui_web.plugin_host_api import prefs_plugin_get

        return prefs_plugin_get(PLUGIN_ID) or {}
    except Exception:
        return {}


def _host_port() -> tuple[str, int]:
    prefs = _prefs()
    host = str(prefs.get("host") or os.environ.get("BLENDER_HOST") or DEFAULT_HOST).strip() or DEFAULT_HOST
    raw_port = prefs.get("port") or os.environ.get("BLENDER_PORT") or DEFAULT_PORT
    try:
        port = int(str(raw_port).strip())
    except (TypeError, ValueError):
        port = DEFAULT_PORT
    return host, port


def _get_conn() -> BlenderConnection:
    global _conn
    host, port = _host_port()
    if _conn is not None and (_conn.host != host or _conn.port != port):
        _conn.disconnect()
        _conn = None
    if _conn is not None:
        try:
            _conn.send_command("get_polyhaven_status")
            return _conn
        except Exception:
            try:
                _conn.disconnect()
            except Exception:
                pass
            _conn = None
    _conn = BlenderConnection(host=host, port=port)
    if not _conn.connect():
        _conn = None
        raise ConnectionError(
            f"Open Blender — addon should auto-start on {host}:{port}. "
            "Restart Blender once after first plugin install. "
            "If Blender was never launched, install it, open once, then call blender_redeploy_addon."
        )
    return _conn


def _cmd(command_type: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return _get_conn().send_command(command_type, params)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


def _process_bbox(original_bbox: list[float] | list[int] | None) -> list[int] | None:
    if original_bbox is None:
        return None
    if all(isinstance(i, int) for i in original_bbox):
        return list(original_bbox)
    if any(float(i) <= 0 for i in original_bbox):
        raise ValueError("bbox values must be > 0")
    mx = max(float(i) for i in original_bbox)
    return [int(float(i) / mx * 100) for i in original_bbox]


def register(api) -> None:
    import os

    # MCP bridge process: skip disk deploy (slow); use blender_redeploy_addon when needed.
    if os.environ.get("UEFN_DUCKY_MCP_BRIDGE") != "1":
        try:
            result = deploy_addon()
            api.log(f"addon deploy: {result}")
        except Exception as exc:
            api.log(f"addon deploy failed: {exc}")
    else:
        api.log("addon deploy skipped (MCP bridge process)")

    @api.tool(name="blender_status", intent=r"\bblender\b")
    def blender_status() -> str:
        """Probe Blender MCP socket + report last addon deploy paths."""
        host, port = _host_port()
        connected = False
        detail: Any = None
        try:
            detail = _cmd("get_scene_info")
            connected = True
        except Exception as exc:
            detail = str(exc)
        roots = []
        try:
            from .deploy_addon import blender_user_roots

            roots = [str(p) for p in blender_user_roots()]
        except Exception:
            pass
        return _dumps(
            {
                "host": host,
                "port": port,
                "connected": connected,
                "detail": detail if not connected else "ok",
                "blender_user_roots": roots,
                "hint": (
                    "Open Blender (restart once after first install)."
                    if not connected
                    else "Ready."
                ),
            }
        )

    @api.tool(name="blender_redeploy_addon", intent=r"\bblender\b")
    def blender_redeploy_addon() -> str:
        """Re-copy the Blender MCP addon into Blender user folders (then restart Blender)."""
        return _dumps(deploy_addon())

    @api.tool(name="blender_get_scene_info", intent=r"\bblender\b")
    def blender_get_scene_info() -> str:
        """Get detailed information about the current Blender scene."""
        try:
            return _dumps(_cmd("get_scene_info"))
        except Exception as exc:
            return f"Error getting scene info: {exc}"

    @api.tool(name="blender_get_object_info", intent=r"\bblender\b")
    def blender_get_object_info(object_name: str) -> str:
        """Get detailed information about a specific object in the Blender scene."""
        try:
            return _dumps(_cmd("get_object_info", {"name": object_name}))
        except Exception as exc:
            return f"Error getting object info: {exc}"

    @api.tool(name="blender_get_viewport_screenshot", intent=r"\bblender\b")
    def blender_get_viewport_screenshot(max_size: int = 1000) -> str:
        """Capture the Blender 3D viewport.

        Returns a short JSON path/media_url payload — never base64. Huge PNG
        blobs poison coding-agent resume sessions and stuck chats.
        """
        try:
            temp_path = os.path.join(
                tempfile.gettempdir(), f"blender_screenshot_{os.getpid()}.png"
            )
            result = _cmd(
                "get_viewport_screenshot",
                {"max_size": max_size, "filepath": temp_path, "format": "png"},
            )
            if "error" in result:
                return f"Error: {result['error']}"
            if not os.path.exists(temp_path):
                return "Error: screenshot file was not created"
            raw = Path(temp_path).read_bytes()
            try:
                os.remove(temp_path)
            except OSError:
                pass
            from frontend.ui_web.tool_captures import save_capture_for_agents
            from mcp.server.fastmcp import Image

            saved = save_capture_for_agents(raw, prefix="blender_viewport")
            payload = {
                "ok": True,
                "format": saved.get("format", "png"),
                "bytes": saved.get("bytes", len(raw)),
                "path": saved.get("path"),
                "capture_path": saved.get("capture_path") or saved.get("path"),
                "filename": saved.get("filename"),
                "media_url": saved.get("media_url"),
                "width": result.get("width"),
                "height": result.get("height"),
                "hint": (
                    "Use project path for file work; media_url/capture_path "
                    "are AppData preview-only. Image also returned as MCP content."
                ),
            }
            text = _dumps(payload)
            project_path = str(saved.get("path") or "")
            if project_path and Path(project_path).is_file():
                return [text, Image(path=project_path)]
            return text
        except Exception as exc:
            return f"Screenshot failed: {exc}"

    @api.tool(name="blender_execute_blender_code", intent=r"\bblender\b")
    def blender_execute_blender_code(code: str) -> str:
        """Execute Python code in Blender. Prefer structured tools; break large edits into steps."""
        try:
            result = _cmd("execute_code", {"code": code})
            return f"Code executed successfully: {result.get('result', '')}"
        except Exception as exc:
            return f"Error executing code: {exc}"

    @api.tool(name="blender_get_polyhaven_status", intent=r"\b(blender|polyhaven)\b")
    def blender_get_polyhaven_status() -> str:
        """Check if Poly Haven integration is enabled in Blender."""
        try:
            result = _cmd("get_polyhaven_status")
            return str(result.get("message") or _dumps(result))
        except Exception as exc:
            return f"Error checking PolyHaven status: {exc}"

    @api.tool(name="blender_get_polyhaven_categories", intent=r"\b(blender|polyhaven)\b")
    def blender_get_polyhaven_categories(asset_type: str = "hdris") -> str:
        """List Poly Haven categories for hdris, textures, models, or all."""
        try:
            result = _cmd("get_polyhaven_categories", {"asset_type": asset_type})
            if "error" in result:
                return f"Error: {result['error']}"
            cats = result.get("categories") or {}
            lines = [f"Categories for {asset_type}:", ""]
            for category, count in sorted(cats.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {category}: {count} assets")
            return "\n".join(lines)
        except Exception as exc:
            return f"Error getting Polyhaven categories: {exc}"

    @api.tool(name="blender_search_polyhaven_assets", intent=r"\b(blender|polyhaven)\b")
    def blender_search_polyhaven_assets(
        asset_type: str = "all",
        categories: str = "",
    ) -> str:
        """Search Poly Haven assets (hdris, textures, models, all)."""
        try:
            result = _cmd(
                "search_polyhaven_assets",
                {
                    "asset_type": asset_type,
                    "categories": categories or None,
                },
            )
            if "error" in result:
                return f"Error: {result['error']}"
            return _dumps(result)
        except Exception as exc:
            return f"Error searching Polyhaven assets: {exc}"

    @api.tool(name="blender_download_polyhaven_asset", intent=r"\b(blender|polyhaven)\b")
    def blender_download_polyhaven_asset(
        asset_id: str,
        asset_type: str,
        resolution: str = "1k",
        file_format: str = "",
    ) -> str:
        """Download and import a Poly Haven asset into Blender."""
        try:
            result = _cmd(
                "download_polyhaven_asset",
                {
                    "asset_id": asset_id,
                    "asset_type": asset_type,
                    "resolution": resolution,
                    "file_format": file_format or None,
                },
            )
            return _dumps(result)
        except Exception as exc:
            return f"Error downloading Polyhaven asset: {exc}"

    @api.tool(name="blender_set_texture", intent=r"\b(blender|polyhaven|texture)\b")
    def blender_set_texture(object_name: str, texture_id: str) -> str:
        """Apply a previously downloaded Poly Haven texture to an object."""
        try:
            return _dumps(
                _cmd("set_texture", {"object_name": object_name, "texture_id": texture_id})
            )
        except Exception as exc:
            return f"Error applying texture: {exc}"

    @api.tool(name="blender_get_sketchfab_status", intent=r"\b(blender|sketchfab)\b")
    def blender_get_sketchfab_status() -> str:
        """Check if Sketchfab integration is enabled in Blender."""
        try:
            result = _cmd("get_sketchfab_status")
            return str(result.get("message") or _dumps(result))
        except Exception as exc:
            return f"Error checking Sketchfab status: {exc}"

    @api.tool(name="blender_search_sketchfab_models", intent=r"\b(blender|sketchfab)\b")
    def blender_search_sketchfab_models(
        query: str,
        categories: str = "",
        count: int = 20,
        downloadable: bool = True,
    ) -> str:
        """Search Sketchfab models (requires API key in Blender addon prefs)."""
        try:
            return _dumps(
                _cmd(
                    "search_sketchfab_models",
                    {
                        "query": query,
                        "categories": categories or None,
                        "count": count,
                        "downloadable": downloadable,
                    },
                )
            )
        except Exception as exc:
            return f"Error searching Sketchfab models: {exc}"

    @api.tool(name="blender_get_sketchfab_model_preview", intent=r"\b(blender|sketchfab)\b")
    def blender_get_sketchfab_model_preview(uid: str) -> str:
        """Get a Sketchfab model thumbnail as JSON with base64 image data."""
        try:
            result = _cmd("get_sketchfab_model_preview", {"uid": uid})
            if "error" in result:
                return f"Error: {result['error']}"
            return _dumps(result)
        except Exception as exc:
            return f"Failed to get preview: {exc}"

    @api.tool(name="blender_download_sketchfab_model", intent=r"\b(blender|sketchfab)\b")
    def blender_download_sketchfab_model(uid: str, target_size: float) -> str:
        """Download/import a Sketchfab model; largest dimension scaled to target_size (meters)."""
        try:
            return _dumps(
                _cmd(
                    "download_sketchfab_model",
                    {
                        "uid": uid,
                        "normalize_size": True,
                        "target_size": target_size,
                    },
                )
            )
        except Exception as exc:
            return f"Error downloading Sketchfab model: {exc}"

    @api.tool(name="blender_get_hyper3d_status", intent=r"\b(blender|hyper3d|rodin)\b")
    def blender_get_hyper3d_status() -> str:
        """Check if Hyper3D Rodin integration is enabled in Blender."""
        try:
            result = _cmd("get_hyper3d_status")
            return str(result.get("message") or _dumps(result))
        except Exception as exc:
            return f"Error checking Hyper3D status: {exc}"

    @api.tool(name="blender_generate_hyper3d_model_via_text", intent=r"\b(blender|hyper3d|rodin)\b")
    def blender_generate_hyper3d_model_via_text(
        text_prompt: str,
        bbox_condition: list[float] | None = None,
    ) -> str:
        """Start a Hyper3D Rodin text-to-3D job. Poll then import_generated_asset."""
        try:
            result = _cmd(
                "create_rodin_job",
                {
                    "text_prompt": text_prompt,
                    "images": None,
                    "bbox_condition": _process_bbox(bbox_condition),
                },
            )
            if result.get("submit_time"):
                return _dumps(
                    {
                        "task_uuid": result["uuid"],
                        "subscription_key": result["jobs"]["subscription_key"],
                    }
                )
            return _dumps(result)
        except Exception as exc:
            return f"Error generating Hyper3D task: {exc}"

    @api.tool(name="blender_generate_hyper3d_model_via_images", intent=r"\b(blender|hyper3d|rodin)\b")
    def blender_generate_hyper3d_model_via_images(
        input_image_paths: list[str] | None = None,
        input_image_urls: list[str] | None = None,
        bbox_condition: list[float] | None = None,
    ) -> str:
        """Start a Hyper3D Rodin image-to-3D job. Pass paths (MAIN_SITE) or urls (FAL_AI)."""
        if input_image_paths and input_image_urls:
            return "Error: Conflict parameters given!"
        if not input_image_paths and not input_image_urls:
            return "Error: No image given!"
        images: Any
        if input_image_paths is not None:
            if not all(os.path.exists(p) for p in input_image_paths):
                return "Error: not all image paths are valid!"
            images = []
            for path in input_image_paths:
                with open(path, "rb") as f:
                    images.append(
                        (Path(path).suffix, base64.b64encode(f.read()).decode("ascii"))
                    )
        else:
            assert input_image_urls is not None
            if not all(urlparse(u).scheme for u in input_image_urls):
                return "Error: not all image URLs are valid!"
            images = list(input_image_urls)
        try:
            result = _cmd(
                "create_rodin_job",
                {
                    "text_prompt": None,
                    "images": images,
                    "bbox_condition": _process_bbox(bbox_condition),
                },
            )
            if result.get("submit_time"):
                return _dumps(
                    {
                        "task_uuid": result["uuid"],
                        "subscription_key": result["jobs"]["subscription_key"],
                    }
                )
            return _dumps(result)
        except Exception as exc:
            return f"Error generating Hyper3D task: {exc}"

    @api.tool(name="blender_poll_rodin_job_status", intent=r"\b(blender|hyper3d|rodin)\b")
    def blender_poll_rodin_job_status(
        subscription_key: str = "",
        request_id: str = "",
    ) -> str:
        """Poll Hyper3D Rodin job until Done/COMPLETED (or failed)."""
        try:
            kwargs: dict[str, Any] = {}
            if subscription_key:
                kwargs["subscription_key"] = subscription_key
            elif request_id:
                kwargs["request_id"] = request_id
            return _dumps(_cmd("poll_rodin_job_status", kwargs))
        except Exception as exc:
            return f"Error polling Hyper3D task: {exc}"

    @api.tool(name="blender_import_generated_asset", intent=r"\b(blender|hyper3d|rodin)\b")
    def blender_import_generated_asset(
        name: str,
        task_uuid: str = "",
        request_id: str = "",
    ) -> str:
        """Import a completed Hyper3D Rodin asset into the Blender scene."""
        try:
            kwargs: dict[str, Any] = {"name": name}
            if task_uuid:
                kwargs["task_uuid"] = task_uuid
            elif request_id:
                kwargs["request_id"] = request_id
            return _dumps(_cmd("import_generated_asset", kwargs))
        except Exception as exc:
            return f"Error importing Hyper3D asset: {exc}"

    @api.tool(name="blender_get_hunyuan3d_status", intent=r"\b(blender|hunyuan)\b")
    def blender_get_hunyuan3d_status() -> str:
        """Check if Hunyuan3D integration is enabled in Blender."""
        try:
            result = _cmd("get_hunyuan3d_status")
            return str(result.get("message") or _dumps(result))
        except Exception as exc:
            return f"Error checking Hunyuan3D status: {exc}"

    @api.tool(name="blender_generate_hunyuan3d_model", intent=r"\b(blender|hunyuan)\b")
    def blender_generate_hunyuan3d_model(
        text_prompt: str = "",
        input_image_url: str = "",
    ) -> str:
        """Start a Hunyuan3D generation job (text and/or image)."""
        try:
            result = _cmd(
                "create_hunyuan_job",
                {
                    "text_prompt": text_prompt or None,
                    "image": input_image_url or None,
                },
            )
            job_id = (result.get("Response") or {}).get("JobId")
            if job_id:
                return _dumps({"job_id": f"job_{job_id}"})
            return _dumps(result)
        except Exception as exc:
            return f"Error generating Hunyuan3D task: {exc}"

    @api.tool(name="blender_poll_hunyuan_job_status", intent=r"\b(blender|hunyuan)\b")
    def blender_poll_hunyuan_job_status(job_id: str = "") -> str:
        """Poll Hunyuan3D job until DONE (or failed)."""
        try:
            return _dumps(_cmd("poll_hunyuan_job_status", {"job_id": job_id}))
        except Exception as exc:
            return f"Error polling Hunyuan3D task: {exc}"

    @api.tool(name="blender_import_generated_asset_hunyuan", intent=r"\b(blender|hunyuan)\b")
    def blender_import_generated_asset_hunyuan(name: str, zip_file_url: str) -> str:
        """Import a completed Hunyuan3D asset from its result zip URL."""
        try:
            return _dumps(
                _cmd(
                    "import_generated_asset_hunyuan",
                    {"name": name, "zip_file_url": zip_file_url},
                )
            )
        except Exception as exc:
            return f"Error importing Hunyuan3D asset: {exc}"

    api.log("blender tools registered")
