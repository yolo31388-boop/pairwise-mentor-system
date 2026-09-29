"""师徒核心兼容入口，实现位于 src/engine.py"""
from src.engine import *  # noqa: F401,F403
from src.engine import MentorRelation, MentorSystem, Player

__all__ = ["MentorRelation", "MentorSystem", "Player"]
