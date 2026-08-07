"""Lessons API: content, per-user progress, and the safe "try it" probe.

Endpoints are gated on the ``lessons`` feature (read). "Try it" runs a
non-destructive, GET-only observation against the two fixed, env-configured lab
target URLs — never a user-supplied URL, never a state change — and returns a
vulnerable-vs-hardened evidence contrast.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session
from .lessons_content import Probe, get_lesson, lesson_detail, lesson_summaries
from .models import LessonProgress, User
from .rbac import require
from .security import SECURITY_HEADERS

router = APIRouter(prefix="/api/lessons")

_HEADER_NAMES = tuple(SECURITY_HEADERS.keys())


async def _observe(client: httpx.AsyncClient, base: str, probe: Probe) -> dict:
    """One non-destructive GET observation against a single target."""
    try:
        resp = await client.get(base.rstrip("/") + probe.path)
    except httpx.HTTPError as exc:
        return {"reachable": False, "error": str(exc)}
    out: dict = {"reachable": True, "status": resp.status_code}
    if probe.kind == "headers":
        out["security_headers_present"] = sum(1 for h in _HEADER_NAMES if h in resp.headers)
        out["max"] = len(_HEADER_NAMES)
    elif probe.kind == "status":
        out["body_contains_marker"] = (
            bool(probe.look_for) and probe.look_for.lower() in resp.text.lower()
        )
    elif probe.kind == "redirect":
        out["location"] = resp.headers.get("location", "")
    return out


async def run_probe(vuln_url: str, secure_url: str, probe: Probe) -> dict:
    """Observe both targets. GET-only, no redirects followed, short timeout."""
    async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
        vulnerable = await _observe(client, vuln_url, probe)
        hardened = await _observe(client, secure_url, probe)
    return {
        "kind": probe.kind,
        "explain": probe.explain,
        "vulnerable": vulnerable,
        "hardened": hardened,
    }


async def _progress_map(session: AsyncSession, user_id: int) -> dict[str, str]:
    rows = (
        await session.execute(
            select(LessonProgress).where(LessonProgress.user_id == user_id)
        )
    ).scalars().all()
    return {r.lesson_key: r.status for r in rows}


@router.get("")
async def list_lessons(
    user: User = Depends(require("lessons", "read")),
    session: AsyncSession = Depends(get_session),
):
    progress = await _progress_map(session, user.id)
    return [
        {**summary, "status": progress.get(summary["key"], "not_started")}
        for summary in lesson_summaries()
    ]


@router.get("/{key}")
async def get_lesson_detail(
    key: str,
    user: User = Depends(require("lessons", "read")),
    session: AsyncSession = Depends(get_session),
):
    lesson = get_lesson(key)
    if lesson is None:
        raise HTTPException(status_code=404, detail="lesson not found")
    progress = await _progress_map(session, user.id)
    return {**lesson_detail(lesson), "status": progress.get(key, "not_started")}


@router.post("/{key}/complete")
async def complete_lesson(
    key: str,
    user: User = Depends(require("lessons", "read")),
    session: AsyncSession = Depends(get_session),
):
    if get_lesson(key) is None:
        raise HTTPException(status_code=404, detail="lesson not found")
    row = (
        await session.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == user.id, LessonProgress.lesson_key == key
            )
        )
    ).scalar_one_or_none()
    if row is None:
        session.add(LessonProgress(user_id=user.id, lesson_key=key, status="completed"))
    else:
        row.status = "completed"
    await session.commit()
    return {"key": key, "status": "completed"}


@router.post("/{key}/try")
async def try_lesson(
    key: str,
    request: Request,
    _: User = Depends(require("lessons", "read")),
):
    lesson = get_lesson(key)
    if lesson is None:
        raise HTTPException(status_code=404, detail="lesson not found")
    if lesson.probe is None:
        return {
            "kind": "none",
            "explain": "This lesson is concept-only; there is no safe live probe.",
        }
    settings = request.app.state.settings
    return await run_probe(settings.vuln_target_url, settings.secure_target_url, lesson.probe)
