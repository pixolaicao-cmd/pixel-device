"""
Supabase 云同步（可选）
- 上传对话记录到 conversations 表
- 拉取 memories 供 Pixel 使用
- 在后台线程静默运行，失败不影响主流程
"""

from __future__ import annotations
import threading
from config import SUPABASE_URL, SUPABASE_KEY, PIXEL_USER_ID

_db = None
_lock = threading.Lock()


def _get_db():
    global _db
    if _db is None and SUPABASE_URL and SUPABASE_KEY:
        from supabase import create_client
        with _lock:
            if _db is None:
                _db = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _db


def _run_bg(fn, *args):
    """在后台线程执行，失败静默。"""
    def _wrapper():
        try:
            fn(*args)
        except Exception as e:
            print(f"[sync] 后台同步失败: {e}")
    threading.Thread(target=_wrapper, daemon=True).start()


def save_message(role: str, content: str):
    """异步保存对话消息到 Supabase。"""
    if not PIXEL_USER_ID:
        return
    def _save():
        db = _get_db()
        if db:
            db.table("conversations").insert({
                "user_id": PIXEL_USER_ID,
                "role": role,
                "content": content,
            }).execute()
    _run_bg(_save)


def get_memories(limit: int = 10) -> list[str]:
    """从 Supabase 拉取最新 memories（阻塞，启动时调用一次）。"""
    if not PIXEL_USER_ID:
        return []
    try:
        db = _get_db()
        if not db:
            return []
        result = (
            db.table("memories")
            .select("content")
            .eq("user_id", PIXEL_USER_ID)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        memories = [m["content"] for m in (result.data or [])]
        print(f"[sync] 已加载 {len(memories)} 条 memories")
        return memories
    except Exception as e:
        print(f"[sync] 拉取 memories 失败: {e}")
        return []


def save_note(title: str, transcript: str):
    """异步保存笔记到 Supabase。"""
    if not PIXEL_USER_ID:
        return
    def _save():
        db = _get_db()
        if db:
            db.table("notes").insert({
                "user_id": PIXEL_USER_ID,
                "title": title,
                "transcript": transcript,
                "summary": "",
                "key_points": [],
            }).execute()
    _run_bg(_save)
