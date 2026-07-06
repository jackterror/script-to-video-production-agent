from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .audit import release_audit, sha256_file
from .io_utils import load_bundle_from_source, load_profile, save_json
from .models import ProjectBundle
from .prompts import derive_shots
from .providers import all_capabilities
from .render import (
    render_before_after,
    render_clean_script,
    render_image_only,
    render_invideo_prompt,
    render_json,
    render_review_sheet,
    render_vendor_prompt,
    render_visual_pack,
)
from .review import apply_review_decisions, audit_scenes, parse_decisions
from .storage import (
    connect,
    load_bundle,
    load_review_issues,
    next_asset,
    overwrite_scenes,
    record_attempt,
    retry_target,
    save_bundle,
    save_review_issues,
    seed_asset_queue,
    update_approval,
)


def add_common_project_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-dir", required=True, type=Path)
    parser.add_argument("--project-id", required=True)


def project_db(project_dir: Path) -> Path:
    return project_dir / "runtime" / "project.sqlite3"


def load_existing_bundle(project_dir: Path, project_id: str) -> ProjectBundle:
    with connect(project_db(project_dir)) as conn:
        return load_bundle(conn, project_id)


def cmd_import(args: argparse.Namespace) -> None:
    profile = load_profile(args.config)
    bundle = load_bundle_from_source(args.input, profile)
    args.project_dir.mkdir(parents=True, exist_ok=True)
    with connect(project_db(args.project_dir)) as conn:
        save_bundle(conn, bundle)
    render_clean_script(bundle, args.project_dir / "outputs" / f"{profile.project_id}-clean.docx", args.project_dir / "outputs" / f"{profile.project_id}-clean.md")
    render_json(args.project_dir / "outputs" / f"{profile.project_id}-scenes.json", {"profile": profile.to_dict(), "scenes": [scene.to_dict() for scene in bundle.scenes]})
    print(args.project_dir)


def cmd_review_export(args: argparse.Namespace) -> None:
    bundle = load_existing_bundle(args.project_dir, args.project_id)
    issues = audit_scenes(bundle.scenes)
    with connect(project_db(args.project_dir)) as conn:
        save_review_issues(conn, bundle.profile.project_id, issues)
    render_review_sheet(bundle, issues, args.project_dir / "outputs" / f"{bundle.profile.project_id}-review.docx", args.project_dir / "outputs" / f"{bundle.profile.project_id}-review.md")
    render_json(args.project_dir / "outputs" / f"{bundle.profile.project_id}-review.json", [issue.to_dict() for issue in issues])
    print(len(issues))


def cmd_review_apply(args: argparse.Namespace) -> None:
    bundle = load_existing_bundle(args.project_dir, args.project_id)
    with connect(project_db(args.project_dir)) as conn:
        issues = load_review_issues(conn, bundle.profile.project_id)
    decisions = parse_decisions(args.decisions.read_text(encoding="utf-8"))
    result = apply_review_decisions(bundle.scenes, issues, decisions)
    updated = ProjectBundle(profile=bundle.profile, scenes=result.updated_scenes, source_path=bundle.source_path)
    with connect(project_db(args.project_dir)) as conn:
        overwrite_scenes(conn, updated)
    render_before_after(
        bundle.profile.title,
        bundle.scenes,
        result.updated_scenes,
        args.project_dir / "outputs" / f"{bundle.profile.project_id}-before-after.docx",
        args.project_dir / "outputs" / f"{bundle.profile.project_id}-before-after.md",
    )
    render_clean_script(updated, args.project_dir / "outputs" / f"{bundle.profile.project_id}-clean-v2.docx", args.project_dir / "outputs" / f"{bundle.profile.project_id}-clean-v2.md")
    print(json.dumps({"accepted": result.accepted, "rejected": result.rejected, "fix_requested": result.fix_requested}, indent=2))


def cmd_export_builder(args: argparse.Namespace) -> None:
    bundle = load_existing_bundle(args.project_dir, args.project_id)
    render_vendor_prompt(bundle, args.project_dir / "outputs" / f"{bundle.profile.project_id}-video-builder.docx", args.project_dir / "outputs" / f"{bundle.profile.project_id}-video-builder.md")
    print("ok")


def cmd_export_invideo(args: argparse.Namespace) -> None:
    bundle = load_existing_bundle(args.project_dir, args.project_id)
    render_invideo_prompt(bundle, args.project_dir / "outputs" / f"{bundle.profile.project_id}-invideo.docx", args.project_dir / "outputs" / f"{bundle.profile.project_id}-invideo.md")
    print("ok")


def cmd_export_visual_pack(args: argparse.Namespace) -> None:
    bundle = load_existing_bundle(args.project_dir, args.project_id)
    render_visual_pack(bundle, args.project_dir / "outputs" / f"{bundle.profile.project_id}-visual-pack.docx", args.project_dir / "outputs" / f"{bundle.profile.project_id}-visual-pack.md")
    print("ok")


def cmd_export_image_only(args: argparse.Namespace) -> None:
    bundle = load_existing_bundle(args.project_dir, args.project_id)
    render_image_only(bundle, args.project_dir / "outputs" / f"{bundle.profile.project_id}-image-only.docx", args.project_dir / "outputs" / f"{bundle.profile.project_id}-image-only.md")
    print("ok")


def cmd_queue_seed(args: argparse.Namespace) -> None:
    bundle = load_existing_bundle(args.project_dir, args.project_id)
    prompts_by_scene = {scene.number: derive_shots(scene, bundle.profile.default_shot_count) for scene in bundle.scenes}
    with connect(project_db(args.project_dir)) as conn:
        seed_asset_queue(conn, bundle, prompts_by_scene, asset_kind=args.asset_kind)
    print("ok")


def cmd_queue_next(args: argparse.Namespace) -> None:
    with connect(project_db(args.project_dir)) as conn:
        payload = next_asset(conn, args.project_id)
    print(json.dumps(payload, indent=2))


def cmd_queue_record(args: argparse.Namespace) -> None:
    with connect(project_db(args.project_dir)) as conn:
        record_attempt(conn, args.target_id, args.provider, args.job_id, args.status, args.output_path, args.last_error)
    print("ok")


def cmd_queue_approve(args: argparse.Namespace) -> None:
    with connect(project_db(args.project_dir)) as conn:
        update_approval(conn, args.target_id, "approved")
    print("ok")


def cmd_queue_reject(args: argparse.Namespace) -> None:
    with connect(project_db(args.project_dir)) as conn:
        update_approval(conn, args.target_id, "rejected")
    print("ok")


def cmd_queue_retry(args: argparse.Namespace) -> None:
    with connect(project_db(args.project_dir)) as conn:
        retry_target(conn, args.target_id, args.reason)
    print("ok")


def cmd_provider_status(args: argparse.Namespace) -> None:
    payload = [cap.__dict__ for cap in all_capabilities()]
    print(json.dumps(payload, indent=2))


def cmd_release_audit(args: argparse.Namespace) -> None:
    findings = release_audit(args.root)
    print(json.dumps(findings, indent=2))
    raise SystemExit(1 if any(findings.values()) else 0)


def cmd_hashes(args: argparse.Namespace) -> None:
    payload: dict[str, Any] = {}
    for path in args.paths:
        payload[str(path)] = sha256_file(path)
    print(json.dumps(payload, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stv-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    import_parser = sub.add_parser("import-script")
    import_parser.add_argument("--input", required=True, type=Path)
    import_parser.add_argument("--config", required=True, type=Path)
    import_parser.add_argument("--project-dir", required=True, type=Path)
    import_parser.set_defaults(func=cmd_import)

    review_export = sub.add_parser("review-export")
    add_common_project_args(review_export)
    review_export.set_defaults(func=cmd_review_export)

    review_apply = sub.add_parser("review-apply")
    add_common_project_args(review_apply)
    review_apply.add_argument("--decisions", required=True, type=Path)
    review_apply.set_defaults(func=cmd_review_apply)

    export_builder = sub.add_parser("export-builder-prompt")
    add_common_project_args(export_builder)
    export_builder.set_defaults(func=cmd_export_builder)

    export_invideo = sub.add_parser("export-invideo-prompt")
    add_common_project_args(export_invideo)
    export_invideo.set_defaults(func=cmd_export_invideo)

    export_visual = sub.add_parser("export-visual-pack")
    add_common_project_args(export_visual)
    export_visual.set_defaults(func=cmd_export_visual_pack)

    export_image = sub.add_parser("export-image-only")
    add_common_project_args(export_image)
    export_image.set_defaults(func=cmd_export_image_only)

    queue_seed = sub.add_parser("queue-seed")
    add_common_project_args(queue_seed)
    queue_seed.add_argument("--asset-kind", choices=["image", "video"], default="image")
    queue_seed.set_defaults(func=cmd_queue_seed)

    queue_next = sub.add_parser("queue-next")
    add_common_project_args(queue_next)
    queue_next.set_defaults(func=cmd_queue_next)

    queue_record = sub.add_parser("queue-record")
    queue_record.add_argument("--project-dir", required=True, type=Path)
    queue_record.add_argument("--target-id", required=True, type=int)
    queue_record.add_argument("--provider", required=True)
    queue_record.add_argument("--job-id")
    queue_record.add_argument("--status", required=True)
    queue_record.add_argument("--output-path")
    queue_record.add_argument("--last-error")
    queue_record.set_defaults(func=cmd_queue_record)

    queue_approve = sub.add_parser("queue-approve")
    queue_approve.add_argument("--project-dir", required=True, type=Path)
    queue_approve.add_argument("--target-id", required=True, type=int)
    queue_approve.set_defaults(func=cmd_queue_approve)

    queue_reject = sub.add_parser("queue-reject")
    queue_reject.add_argument("--project-dir", required=True, type=Path)
    queue_reject.add_argument("--target-id", required=True, type=int)
    queue_reject.set_defaults(func=cmd_queue_reject)

    queue_retry = sub.add_parser("queue-retry")
    queue_retry.add_argument("--project-dir", required=True, type=Path)
    queue_retry.add_argument("--target-id", required=True, type=int)
    queue_retry.add_argument("--reason", required=True)
    queue_retry.set_defaults(func=cmd_queue_retry)

    provider_status = sub.add_parser("provider-status")
    provider_status.set_defaults(func=cmd_provider_status)

    audit_parser = sub.add_parser("release-audit")
    audit_parser.add_argument("root", type=Path)
    audit_parser.set_defaults(func=cmd_release_audit)

    hashes = sub.add_parser("hashes")
    hashes.add_argument("paths", nargs="+", type=Path)
    hashes.set_defaults(func=cmd_hashes)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0
