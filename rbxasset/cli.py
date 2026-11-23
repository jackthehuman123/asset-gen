"""Command line: build / sample / new / deliver. Exit codes: 0 ok, 1 build failure, 2 validation error."""

import argparse
import json
import sys
import zlib
from pathlib import Path
from typing import Dict, List, Optional

from rbxasset import assemble, match, store
from rbxasset.builders import REGISTRY, load_vocab
from rbxasset.config import ConfigError, load_config
from rbxasset.runner import BuildError, run_blender
from rbxasset.upload import ModerationRejected, OpenCloud, UploadError, deliver_uploads
from rbxasset.spec import SpecError, load_spec
from rbxasset.style import StyleError, load_style


def _job(mode, spec, style, vocab, asset, out_dir, tiles, manifest) -> Dict:
    return {
        "mode": mode,
        "spec": spec.to_dict(),
        "style": {
            "studs_per_tile": style.studs_per_tile,
            "budgets": style.budgets,
            "lighting": style.lighting,
        },
        "vocab": {
            "tiled_tags": sorted(vocab.tiled_tags),
            "big_tags": sorted(vocab.big_tags),
            "no_collide_tags": sorted(vocab.no_collide_tags),
        },
        "asset": asset,
        "out_dir": str(out_dir),
        "tiles_dir": str(tiles),
        "manifest_path": str(manifest),
    }


def _print_result(manifest: Dict, table: bool) -> None:
    if table:
        print("%-22s %8s  %s" % ("mesh", "tris", "tiled"))
        for m in manifest["meshes"]:
            print(
                "%-22s %8d  %s" % (m["name"], m["tris"], "yes" if m["tiled"] else "no")
            )
    for p in manifest["previews"]:
        print("preview: %s" % p)


def _peek_area(spec_path: Path) -> Optional[str]:
    try:
        area = json.loads(Path(spec_path).read_text(encoding="utf-8")).get("area")
    except (OSError, ValueError, AttributeError):
        return None  # load_spec reports missing or broken specs
    return area if isinstance(area, str) else None


def _load(root: Path, ref: str, spec_path: Path):
    game, asset = store.split_ref(ref)
    cfg = load_config(root)
    game_md = store.game_style_path(root, game, asset)
    if not game_md.is_file():
        raise StyleError("no STYLE.md for game '%s' at %s" % (game, game_md))
    area = _peek_area(spec_path)
    area_md = store.area_style_path(root, game, area) if area else None
    if area_md is not None and not area_md.is_file():
        raise StyleError("no STYLE.md for area '%s' at %s" % (area, area_md))
    style = load_style(game_md, area_md)
    spec = load_spec(spec_path, style)
    return cfg, style, spec


def cmd_build(root: Path, ref: str) -> int:
    paths = store.asset_paths(root, ref)
    cfg, style, spec = _load(root, ref, paths.spec)
    vocab = load_vocab(spec.builder)
    job = _job(
        "build",
        spec,
        style,
        vocab,
        ref,
        paths.out,
        store.tiles_dir(root, store.split_ref(ref)[0]),
        paths.manifest,
    )
    _print_result(run_blender(cfg, job), table=True)
    return 0


def cmd_sample(root: Path, ref: str, variants: List[str]) -> int:
    paths = store.asset_paths(root, ref)
    game = store.split_ref(ref)[0]
    loaded = []
    for v in variants:  # validate everything before starting Blender
        vp = Path(v)
        if not vp.exists():
            vp = paths.dir / "variants" / v
        loaded.append((vp.stem,) + _load(root, ref, vp))
    for stem, cfg, style, spec in loaded:
        out = paths.samples / stem
        job = _job(
            "sample",
            spec,
            style,
            load_vocab(spec.builder),
            ref,
            out,
            store.tiles_dir(root, game),
            out / "manifest.json",
        )
        print("sample: %s" % stem)
        _print_result(run_blender(cfg, job), table=False)
    return 0


def cmd_new(root: Path, ref: str, builder: str) -> int:
    paths = store.asset_paths(root, ref)
    if builder not in REGISTRY:
        raise SpecError(
            "unknown builder %r; available: %s" % (builder, ", ".join(sorted(REGISTRY)))
        )
    if paths.spec.exists():
        raise SpecError("%s already exists" % paths.spec)
    vocab = load_vocab(builder)
    spec = {
        "builder": builder,
        "brief": "",
        "seed": 1,
        "params": {
            k: (p.default if p.default is not None else "TODO")
            for k, p in vocab.params.items()
        },
        "parts": {t: "TODO" for t in vocab.part_tags},
    }
    paths.dir.mkdir(parents=True, exist_ok=True)
    paths.spec.write_text(json.dumps(spec, indent=2) + "\n")
    print("wrote %s" % paths.spec)
    return 0


def cmd_match(request: str) -> int:
    if not request.strip():
        raise SpecError("match needs a description of the asset")
    ms = match.match_all(request)
    for m in ms:
        print(
            "%-10s %.2f  %s"
            % (m.builder, m.confidence, "; ".join(m.reasons) or "no fit")
        )
    kind, best = match.verdict(ms)
    print("verdict: %s%s" % (kind, " (best: %s)" % best.builder if best else ""))
    return 0


def _fake_ids(manifest: Dict, paths) -> Dict[str, str]:
    files = [str(paths.fbx)]
    for m in manifest.get("meshes", []):
        files.extend(str(p) for p in m.get("maps", {}).values())
    files.extend(str(d["image"]) for d in manifest.get("decals", []))
    return {f: str(1000000 + zlib.crc32(f.encode("utf-8")) % 9000000) for f in files}


def cmd_deliver(root: Path, ref: str, dry_run: bool) -> int:
    paths = store.asset_paths(root, ref)
    if not paths.manifest.is_file():
        raise SpecError("%s not found; run build first" % paths.manifest)
    try:
        manifest = json.loads(paths.manifest.read_text())
    except ValueError as e:
        raise SpecError("%s is not valid JSON (%s); rebuild" % (paths.manifest, e))
    if dry_run:
        ids = _fake_ids(manifest, paths)
    else:
        cfg = load_config(root, require_key=True)
        client = OpenCloud(cfg.api_key, cfg.creator_type, cfg.creator_id)
        ids = deliver_uploads(manifest, paths, client)
    paths.assemble.parent.mkdir(parents=True, exist_ok=True)
    paths.assemble.write_text(
        assemble.generate_luau(manifest, ids, store.split_ref(ref)[1])
    )
    print("wrote %s" % paths.assemble)
    print(
        "Run it via the Studio MCP run-code tool, or paste it into Studio's Command Bar."
    )
    return 0


def main(argv: Optional[List[str]] = None, root: Optional[Path] = None) -> int:
    ap = argparse.ArgumentParser(prog="rbxasset")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("asset")
    s = sub.add_parser("sample")
    s.add_argument("asset")
    s.add_argument("variants", nargs="+")
    n = sub.add_parser("new")
    n.add_argument("asset")
    n.add_argument("--builder", required=True)
    mt = sub.add_parser("match")
    mt.add_argument("request", nargs="+")
    dl = sub.add_parser("deliver")
    dl.add_argument("asset")
    dl.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    root = Path(root) if root else Path.cwd()
    try:
        if args.cmd == "match":
            return cmd_match(" ".join(args.request))
        if args.cmd == "build":
            return cmd_build(root, args.asset)
        if args.cmd == "sample":
            return cmd_sample(root, args.asset, args.variants)
        if args.cmd == "deliver":
            return cmd_deliver(root, args.asset, args.dry_run)
        return cmd_new(root, args.asset, args.builder)
    except (SpecError, StyleError, ConfigError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    except (UploadError, ModerationRejected) as e:
        print("upload failed: %s" % e, file=sys.stderr)
        return 1
    except BuildError as e:
        print("build failed: %s" % e, file=sys.stderr)
        return 1
    except OSError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
