import json
import shutil
import struct
import zlib
from pathlib import Path

import pytest

from rbxasset import cli

FIX = Path(__file__).parent / "fixtures"


def png_rgba_pixel(path, x, y):
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w, h, ctype, depth = 8, b"", 0, 0, 0, 0
    while pos < len(data):
        ln, = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT":
            idat += body
        pos += 12 + ln
    assert ctype == 6 and depth == 8, "decal must be 8-bit RGBA"
    raw = zlib.decompress(idat)
    bpp, stride = 4, w * 4
    rows, prev = [], bytearray(stride)
    for r in range(h):
        off = r * (stride + 1)
        f, line = raw[off], bytearray(raw[off + 1:off + 1 + stride])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        rows.append(line)
        prev = line
    px = rows[y][x * 4:x * 4 + 4]
    return tuple(px)


@pytest.mark.blender
def test_cabinet_build_end_to_end(tmp_path):
    root = tmp_path / "proj"
    (root / "game" / "areas" / "farm").mkdir(parents=True)
    # low budgets keep the test fast; preview_* keys are optional render knobs
    game = (FIX / "game_STYLE.md").read_text().replace(
        '"camera": "first_person",',
        '"camera": "first_person", "budgets": {"texture_big": 256, "texture_small": 128,'
        ' "preview_samples": 8, "preview_res": [400, 300]},')
    (root / "game" / "STYLE.md").write_text(game)
    shutil.copy(FIX / "area_STYLE.md", root / "game" / "areas" / "farm" / "STYLE.md")
    (root / "rbxasset.config.json").write_text(
        (Path(__file__).parent.parent / "rbxasset.config.json").read_text())
    adir = root / "assets" / "farm" / "cabinet"
    adir.mkdir(parents=True)
    shutil.copy(FIX / "cabinet_spec.json", adir / "spec.json")

    assert cli.main(["build", "farm/cabinet"], root=root) == 0

    out = adir / "out"
    m = json.loads((out / "manifest.json").read_text())
    assert len(m["meshes"]) == 6 and all(x["tris"] < 20000 for x in m["meshes"])
    by = {x["name"].split("_", 1)[1]: x for x in m["meshes"]}
    for x in m["meshes"]:
        if not x["tiled"]:
            for k in ("color", "roughness", "normal"):
                assert Path(x["maps"][k]).is_file(), (x["name"], k)
    assert Path(by["handles"]["maps"]["metalness"]).is_file()
    assert Path(m["fbx"]).is_file()
    assert len([p for p in m["previews"] if Path(p).is_file()]) >= 2
    assert len(m["decals"]) == 1
    d = m["decals"][0]
    assert d["on"] == "fronts"
    assert png_rgba_pixel(d["image"], 0, 0)[3] == 0
