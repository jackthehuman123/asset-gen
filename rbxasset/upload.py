"""Open Cloud asset upload with a content-hash cache (roblox.json) and resume.

NOTE: the request/response shapes below are UNVERIFIED until Task 1's live
delivery spike (docs/findings/delivery.md). They follow the intended spec 5.4
shapes; correct them in the constants/helpers in the "wire format" section.

deliver_uploads returns {file_path: asset_id} for every uploaded or cached,
non-rejected file. Rejected decals are ABSENT from the result (recorded in
roblox.json with rejected=true); callers should omit decals whose image is
not in the result.

Known limitations (need Task 1 data to solve):
- Retrying a POST after a timeout can create a duplicate asset if the first
  request actually reached Roblox.
- A crash between the POST and operation completion orphans that asset; the
  rerun re-uploads the file.
"""

import hashlib
import http.client
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from rbxasset.store import AssetPaths

# --- wire format (unverified until Task 1) ---------------------------------
ASSETS_PATH = "/assets/v1/assets"
OPERATIONS_PATH = "/assets/v1/operations/"
API_KEY_HEADER = "x-api-key"
CONTENT_TYPES = {"Model": "model/fbx", "Decal": "image/png"}
REJECTED_STATE = "Rejected"


def build_request_json(
    asset_type: str, display_name: str, creator_type: str, creator_id: str
) -> str:
    key = "groupId" if creator_type == "group" else "userId"
    return json.dumps(
        {
            "assetType": asset_type,
            "displayName": display_name,
            "description": "rbxasset",
            "creationContext": {"creator": {key: str(creator_id)}},
        }
    )


def operation_id(op: Dict) -> str:
    return str(op["path"]).rsplit("/", 1)[1]


def asset_id_of(op: Dict) -> str:
    return str(op["response"]["assetId"])


def is_rejected(op: Dict) -> bool:
    mod = op.get("response", {}).get("moderationResult", {})
    return mod.get("moderationState") == REJECTED_STATE


# ---------------------------------------------------------------------------

AUTH_MESSAGE = (
    "Open Cloud rejected the API key or creator. Check ROBLOX_API_KEY has Assets "
    "read+write and creator_type/creator_id match the game's owner (user vs group)."
)
BACKOFF = (1, 2, 4, 8, 16)


class UploadError(Exception):
    pass


class ModerationRejected(UploadError):
    def __init__(self, path: Path, message: Optional[str] = None):
        super().__init__(message or "Roblox moderation rejected %s" % path)
        self.path = Path(path)


def _multipart(
    fields: List[Tuple[str, Optional[str], str, bytes]],
) -> Tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    out = b""
    for name, filename, ctype, data in fields:
        disp = 'form-data; name="%s"' % name
        if filename:
            disp += '; filename="%s"' % filename
        out += (
            (
                "--%s\r\nContent-Disposition: %s\r\nContent-Type: %s\r\n\r\n"
                % (boundary, disp, ctype)
            ).encode()
            + data
            + b"\r\n"
        )
    out += ("--%s--\r\n" % boundary).encode()
    return out, "multipart/form-data; boundary=" + boundary


class OpenCloud:
    def __init__(
        self,
        api_key: str,
        creator_type: str,
        creator_id: str,
        base_url: str = "https://apis.roblox.com",
        poll_interval: float = 1.0,
        max_polls: int = 120,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.api_key = api_key
        self.creator_type = creator_type
        self.creator_id = creator_id
        self.base_url = base_url.rstrip("/")
        self.poll_interval = poll_interval
        self.max_polls = max_polls
        self.sleep = sleep

    def _send(self, req_factory: Callable[[], urllib.request.Request]) -> Dict:
        for attempt in range(len(BACKOFF) + 1):
            retry = False
            try:
                with urllib.request.urlopen(req_factory(), timeout=60) as resp:
                    raw = resp.read()
                try:
                    data = json.loads(raw.decode() or "{}")
                except ValueError:  # includes UnicodeDecodeError and JSONDecodeError
                    raise UploadError(
                        "unexpected Open Cloud response: %s"
                        % raw.decode("utf-8", "replace")[:300]
                    ) from None
                if not isinstance(data, dict):
                    raise UploadError(
                        "unexpected Open Cloud response: %s" % str(data)[:300]
                    )
                return data
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    raise UploadError(AUTH_MESSAGE) from None
                if e.code == 429 or e.code >= 500:
                    retry = True
                else:
                    raise UploadError(
                        "Open Cloud error %d: %s"
                        % (e.code, e.read().decode(errors="replace")[:300])
                    ) from None
            except (
                OSError,
                http.client.HTTPException,
            ):  # URLError, timeouts, resets, bad status line
                retry = True
            if retry:
                if attempt >= len(BACKOFF):
                    raise UploadError(
                        "Open Cloud unavailable after %d retries" % len(BACKOFF)
                    ) from None
                self.sleep(BACKOFF[attempt])
        raise UploadError("unreachable")

    @staticmethod
    def _shape(fn, op):
        try:
            return fn(op)
        except (KeyError, IndexError, TypeError, AttributeError):
            raise UploadError(
                "unexpected Open Cloud response: %s" % json.dumps(op)[:300]
            ) from None

    def upload(self, path: Path, asset_type: str, display_name: str) -> str:
        path = Path(path)
        body, ctype = _multipart(
            [
                (
                    "request",
                    None,
                    "application/json",
                    build_request_json(
                        asset_type, display_name, self.creator_type, self.creator_id
                    ).encode(),
                ),
                (
                    "fileContent",
                    path.name,
                    CONTENT_TYPES[asset_type],
                    path.read_bytes(),
                ),
            ]
        )

        def make_post():
            return urllib.request.Request(
                self.base_url + ASSETS_PATH,
                data=body,
                method="POST",
                headers={API_KEY_HEADER: self.api_key, "Content-Type": ctype},
            )

        op = self._send(make_post)
        op_id = self._shape(operation_id, op)
        for _ in range(self.max_polls):
            if op.get("done"):
                if self._shape(is_rejected, op):
                    raise ModerationRejected(path)
                return self._shape(asset_id_of, op)
            self.sleep(self.poll_interval)
            op = self._send(
                lambda: urllib.request.Request(
                    self.base_url + OPERATIONS_PATH + op_id,
                    headers={API_KEY_HEADER: self.api_key},
                )
            )
        if op.get("done"):
            if self._shape(is_rejected, op):
                raise ModerationRejected(path)
            return self._shape(asset_id_of, op)
        raise UploadError("Timed out waiting for operation %s" % op_id)


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def deliver_uploads(
    manifest: Dict, paths: AssetPaths, client: OpenCloud
) -> Dict[str, str]:
    cache_path = paths.roblox
    cache: Dict = {"files": {}}
    if cache_path.is_file():
        try:
            cache = json.loads(cache_path.read_text())
            cache.setdefault("files", {})
        except (ValueError, AttributeError):
            raise UploadError(
                "%s is corrupt. Delete it to re-upload everything (existing Roblox "
                "assets will be duplicated), or restore it from backup." % cache_path
            ) from None

    work: List[Tuple[str, str, bool]] = [(str(paths.fbx), "Model", False)]
    for mesh in manifest.get("meshes", []):
        for p in mesh.get("maps", {}).values():
            work.append((str(p), "Decal", False))
    for d in manifest.get("decals", []):
        work.append((str(d["image"]), "Decal", True))

    result: Dict[str, str] = {}
    for fpath, atype, is_decal in work:
        digest = _sha256(Path(fpath))
        entry = cache["files"].get(digest)
        if entry is not None and (
            entry.get("creator_type", client.creator_type) != client.creator_type
            or str(entry.get("creator_id", client.creator_id)) != str(client.creator_id)
        ):
            entry = None  # uploaded under a different owner: re-upload
        if entry is None:
            name = Path(fpath).stem
            owner = {
                "creator_type": client.creator_type,
                "creator_id": str(client.creator_id),
            }
            try:
                entry = {
                    "id": client.upload(Path(fpath), atype, name),
                    "type": atype,
                    "name": name,
                    "rejected": False,
                    **owner,
                }
            except ModerationRejected:
                entry = {
                    "id": "",
                    "type": atype,
                    "name": name,
                    "rejected": True,
                    **owner,
                }
            cache["files"][digest] = entry
            tmp = cache_path.with_name(cache_path.name + ".tmp")
            tmp.write_text(json.dumps(cache, indent=2))
            os.replace(str(tmp), str(cache_path))
        if entry["rejected"]:
            if is_decal:
                continue
            raise ModerationRejected(
                Path(fpath),
                (
                    "Roblox moderation rejected %s (%s); asset delivery stopped. If this is "
                    "a false positive, remove hash %s from %s and rerun."
                    % (Path(fpath).name, atype, digest, cache_path)
                ),
            )
        result[fpath] = entry["id"]
    return result
