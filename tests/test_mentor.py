"""师徒系统行为测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.engine import (
    DISSOLVE_COOLDOWN_SECONDS,
    MAX_ACTIVE_APPRENTICES,
    MentorSystem,
)


def make_system():
    ms = MentorSystem()
    ms.register_player("mentor", level=50, teaching_rating=90)
    ms.register_player("apprentice", level=10)
    return ms


class TestMentor:
    def test_mentor_qualification(self):
        ms = make_system()
        assert ms.can_mentor("mentor", "apprentice")
        assert not ms.can_mentor("mentor", "mentor")
        # 师傅等级不足
        ms.register_player("low_level", level=10, teaching_rating=90)
        assert not ms.can_mentor("low_level", "apprentice")
        # 教学评分不足
        ms.register_player("low_rating", level=50, teaching_rating=10)
        assert not ms.can_mentor("low_rating", "apprentice")
        # 当前徒弟数达到上限后不能再收
        for i in range(MAX_ACTIVE_APPRENTICES):
            ms.register_player(f"app{i}", level=5)
            ms.start_apprenticeship("mentor", f"app{i}")
        ms.register_player("one_more", level=5)
        assert not ms.can_mentor("mentor", "one_more")

    def test_apprentice_eligibility(self):
        ms = make_system()
        ms.start_apprenticeship("mentor", "apprentice")
        ms.register_player("mentor2", level=60, teaching_rating=80)
        # 徒弟已有师傅不能再拜
        assert not ms.can_mentor("mentor2", "apprentice")
        # 徒弟等级超过上限
        ms.register_player("veteran", level=50)
        assert not ms.can_mentor("mentor2", "veteran")
        # 等级差不足
        ms.register_player("weak_mentor", level=35, teaching_rating=90)
        ms.register_player("almost", level=29)
        assert not ms.can_mentor("weak_mentor", "almost")


class TestReward:
    def test_reward_scales_with_count(self):
        ms = MentorSystem()
        first = ms.graduate_reward("m1")
        second = ms.graduate_reward("m1")
        third = ms.graduate_reward("m1", quality="excellent")
        # 带徒弟越多奖励越高
        assert second["gold"] > first["gold"]
        # 出师质量越高奖励越高
        assert third["gold"] > second["gold"]
        # 累计奖励
        assert second["total_gold"] == first["gold"] + second["gold"]
        assert third["total_gold"] == first["gold"] + second["gold"] + third["gold"]
        assert third["graduated_count"] == 3


class TestTask:
    def test_shared_task_progress(self):
        ms = make_system()
        ms.start_apprenticeship("mentor", "apprentice")
        # 师傅和徒弟推进的是同一份进度
        assert ms.update_task(0, "daily", 3, "mentor")
        assert ms.update_task(0, "daily", 2, "apprentice")
        rel = ms.relations[0]
        assert rel.progress["daily"] == 5
        # 关系外的人不能推进
        assert not ms.update_task(0, "daily", 1, "outsider")
        assert rel.progress["daily"] == 5


class TestDissolve:
    def test_cooldown_and_penalty(self):
        ms = make_system()
        ms.start_apprenticeship("mentor", "apprentice", now=0)
        earned = ms.graduate_reward("mentor", quality="good")
        result = ms.end_relation(0, now=100)
        # 惩罚：扣除部分累计奖励
        assert result["penalty_gold"] > 0
        assert result["total_gold"] == earned["total_gold"] - result["penalty_gold"]
        assert result["cooldown_until"] == 100 + DISSOLVE_COOLDOWN_SECONDS
        # 冷却期内师傅不能再收徒、徒弟不能再拜师
        ms.register_player("new_app", level=5)
        ms.register_player("mentor2", level=60, teaching_rating=80)
        assert not ms.can_mentor("mentor", "new_app", now=100 + 3600)
        assert not ms.can_mentor("mentor2", "apprentice", now=100 + 3600)
        # 冷却结束后可以重新拜师
        assert ms.can_mentor("mentor", "new_app",
                             now=100 + DISSOLVE_COOLDOWN_SECONDS + 1)


class TestBonus:
    def test_inheritance_bonus_always_on(self):
        ms = make_system()
        assert ms.get_apprentice_bonus("apprentice") == {}
        ms.start_apprenticeship("mentor", "apprentice")
        # 不组队也有常驻基础加成
        solo = ms.get_apprentice_bonus("apprentice")
        assert solo["attack"] > 0
        assert solo["defense"] > 0
        assert solo["hp"] > 0
        # 组队时有额外加成
        party = ms.get_apprentice_bonus("apprentice", in_party=True)
        assert party["attack"] > solo["attack"]
        assert party["defense"] > solo["defense"]
        assert party["hp"] > solo["hp"]
