import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from rbxasset import upload
from rbxasset.store import AssetPaths
from rbxasset.upload import ModerationRejected, OpenCloud, UploadError, deliver_uploads


class Fake:
    def __init__(self):
        self.posts = []  # (headers, body bytes)
        self.gets = []
        self.post_hook = None  # fn(n) -> (status, obj) or None for default
        self.reject = set()  # filenames (from request JSON displayName) to reject
        self.polls_needed = 1
        self.ops = {}

    def start(self):
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, status, obj):
                data = json.dumps(obj).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                fake.posts.append((dict(self.headers), body))
                n = len(fake.posts)
                if fake.post_hook:
                    r = fake.post_hook(n)
                    if r:
                        return self._send(*r)
                name = body.split(b'"displayName": "')[1].split(b'"')[0].decode()
                op = "op%d" % n
                fake.ops[op] = {"left": fake.polls_needed, "name": name, "id": str(1000 + n)}
                self._send(200, {"path": "operations/" + op, "done": False})

            def do_GET(self):
                fake.gets.append(self.path)
                op = fake.ops[self.path.rsplit("/", 1)[1]]
                op["left"] -= 1
                if op["left"] > 0:
                    return self._send(200, {"path": self.path, "done": False})
                state = "Rejected" if op["name"] in fake.reject else "Approved"
                self._send(200, {"done": True, "response": {
                    "assetId": op["id"], "moderationResult": {"moderationState": state}}})

        self.server = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = "http://127.0.0.1:%d" % self.server.server_port
        return self

    def stop(self):
        self.server.shutdown()


@pytest.fixture
def fake():
    f = Fake().start()
    yield f
    f.stop()


def client(fake, ctype="user"):
    return OpenCloud("KEY", ctype, "42", base_url=fake.url, poll_interval=0,
                     sleep=lambda s: None)


def make_asset(tmp_path, n_maps=2, decal=True):
    d = tmp_path / "a"
    d.mkdir()
    paths = AssetPaths(dir=d) if "dir" in AssetPaths.__dataclass_fields__ else AssetPaths(d)
    paths.out.mkdir(parents=True, exist_ok=True)
    paths.textures.mkdir(parents=True, exist_ok=True)
    paths.fbx.write_bytes(b"fbxdata")
    maps = {}
    for i in range(n_maps):
        p = paths.textures / ("m%d.png" % i)
        p.write_bytes(b"map%d" % i)
        maps["k%d" % i] = str(p)
    decals = []
    if decal:
        p = paths.textures / "sign.png"
        p.write_bytes(b"decal")
        decals.append({"name": "sign", "image": str(p)})
    manifest = {"meshes": [{"name": "m", "maps": maps}], "decals": decals}
    return manifest, paths


def test_upload_polls_operation_until_done(fake, tmp_path):
    fake.polls_needed = 3
    f = tmp_path / "x.png"
    f.write_bytes(b"png")
    aid = client(fake, "group").upload(f, "Decal", "x")
    assert aid == "1001"
    assert len(fake.gets) == 3
    headers, body = fake.posts[0]
    assert {k.lower(): v for k, v in headers.items()}["x-api-key"] == "KEY"
    assert b'name="request"' in body and b"image/png" in body
    assert b'"groupId": "42"' in body


def test_auth_failure_message_mentions_user_vs_group(fake, tmp_path):
    fake.post_hook = lambda n: (403, {"error": "no"})
    f = tmp_path / "x.png"
    f.write_bytes(b"png")
    with pytest.raises(UploadError, match="user vs group"):
        client(fake).upload(f, "Decal", "x")


def test_429_retries_then_succeeds(fake, tmp_path):
    fake.post_hook = lambda n: (429, {}) if n <= 2 else None
    sleeps = []
    c = OpenCloud("K", "user", "1", base_url=fake.url, poll_interval=0, sleep=sleeps.append)
    f = tmp_path / "x.png"
    f.write_bytes(b"png")
    assert c.upload(f, "Decal", "x")
    assert sleeps[:2] == [1, 2]


def test_redeliver_skips_cached_files(fake, tmp_path):
    manifest, paths = make_asset(tmp_path)
    first = deliver_uploads(manifest, paths, client(fake))
    assert len(first) == 4
    n = len(fake.posts)
    assert deliver_uploads(manifest, paths, client(fake)) == first
    assert len(fake.posts) == n


def test_changed_file_reuploads_only_that_file(fake, tmp_path):
    manifest, paths = make_asset(tmp_path)
    deliver_uploads(manifest, paths, client(fake))
    n = len(fake.posts)
    Path(manifest["meshes"][0]["maps"]["k0"]).write_bytes(b"changed")
    deliver_uploads(manifest, paths, client(fake))
    assert len(fake.posts) == n + 1


def test_shared_maps_upload_once(fake, tmp_path):
    manifest, paths = make_asset(tmp_path, decal=False)
    manifest["meshes"].append({"name": "n", "maps": dict(manifest["meshes"][0]["maps"])})
    deliver_uploads(manifest, paths, client(fake))
    assert len(fake.posts) == 3


def test_resume_after_crash(fake, tmp_path):
    manifest, paths = make_asset(tmp_path)
    fake.post_hook = lambda n: (500, {}) if 3 <= n <= 8 else None
    with pytest.raises(UploadError):
        deliver_uploads(manifest, paths, client(fake))
    assert len(json.loads(paths.roblox.read_text())["files"]) == 2
    fake.post_hook = None
    n = len(fake.posts)
    result = deliver_uploads(manifest, paths, client(fake))
    assert len(fake.posts) == n + 2
    assert len(result) == 4


def test_rejected_decal_does_not_block(fake, tmp_path):
    manifest, paths = make_asset(tmp_path)
    fake.reject = {"sign"}
    result = deliver_uploads(manifest, paths, client(fake))
    assert manifest["decals"][0]["image"] not in result
    assert len(result) == 3
    files = json.loads(paths.roblox.read_text())["files"]
    assert sum(1 for v in files.values() if v["rejected"]) == 1
    n = len(fake.posts)
    deliver_uploads(manifest, paths, client(fake))
    assert len(fake.posts) == n


def test_rejected_texture_raises_after_saving_cache(fake, tmp_path):
    manifest, paths = make_asset(tmp_path)
    fake.reject = {"m0"}
    with pytest.raises(ModerationRejected) as e:
        deliver_uploads(manifest, paths, client(fake))
    assert e.value.path.name == "m0.png"
    files = json.loads(paths.roblox.read_text())["files"]
    assert any(v["rejected"] for v in files.values())
