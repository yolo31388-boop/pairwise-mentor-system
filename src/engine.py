"""师徒系统"""
import time
from dataclasses import dataclass, field

MIN_MENTOR_LEVEL = 30            # 师傅最低等级
MAX_APPRENTICE_LEVEL = 29        # 徒弟等级上限
MIN_TEACHING_RATING = 60         # 师傅最低教学评分
MAX_ACTIVE_APPRENTICES = 3       # 同时可带徒弟数
DISSOLVE_COOLDOWN = 7 * 86400    # 解除关系冷却：7 天
DISSOLVE_PENALTY_RATE = 0.3      # 解除惩罚：扣除累计奖励比例
BASE_REWARD_GOLD = 1000
QUALITY_MULTIPLIER = {"poor": 0.5, "normal": 1.0, "good": 1.5, "excellent": 2.0}
BASE_BONUS = {"attack": 5, "defense": 5, "hp": 50}      # 常驻基础加成
PARTY_BONUS = {"attack": 15, "defense": 15, "hp": 150}  # 组队额外加成


@dataclass
class Player:
    level: int = 1
    teaching_rating: int = 0
    graduated_count: int = 0      # 已出师徒弟数
    total_reward_gold: int = 0    # 累计出师奖励
    cooldown_until: float = 0.0   # 解除关系冷却截止时间


@dataclass
class MentorRelation:
    mentor: str
    apprentice: str
    progress: dict
    status: str = "active"
    started_at: float = 0.0
    ended_at: float = 0.0
    contributors: dict = field(default_factory=dict)


class MentorSystem:
    def __init__(self, clock=time.time):
        self.relations: list[MentorRelation] = []
        self.players: dict[str, Player] = {}
        self.mentor_rating = {}
        self._clock = clock

    def _now(self, now=None):
        return self._clock() if now is None else now

    def register_player(self, player_id, level=1, teaching_rating=0):
        player = Player(level=level, teaching_rating=teaching_rating)
        self.players[player_id] = player
        self.mentor_rating[player_id] = teaching_rating
        return player

    def _player(self, player_id):
        return self.players.get(player_id, Player())

    def _active_apprentices(self, mentor_id):
        return [r for r in self.relations
                if r.mentor == mentor_id and r.status == "active"]

    def _has_active_mentor(self, apprentice_id):
        return any(r.apprentice == apprentice_id and r.status == "active"
                   for r in self.relations)

    def can_mentor(self, mentor_id, apprentice_id, now=None):
        now = self._now(now)
        if mentor_id == apprentice_id:
            return False
        mentor = self._player(mentor_id)
        apprentice = self._player(apprentice_id)
        if mentor.level < MIN_MENTOR_LEVEL:
            return False
        if mentor.teaching_rating < MIN_TEACHING_RATING:
            return False
        if len(self._active_apprentices(mentor_id)) >= MAX_ACTIVE_APPRENTICES:
            return False
        if self._has_active_mentor(apprentice_id):
            return False
        if apprentice.level > MAX_APPRENTICE_LEVEL:
            return False
        if mentor.cooldown_until > now or apprentice.cooldown_until > now:
            return False
        return True

    def start_apprenticeship(self, mentor, apprentice, now=None):
        now = self._now(now)
        if not self.can_mentor(mentor, apprentice, now):
            raise ValueError("不满足拜师条件")
        rel = MentorRelation(mentor, apprentice, {}, started_at=now)
        self.relations.append(rel)
        return rel

    def graduate_reward(self, mentor_id, quality="normal"):
        mentor = self._player(mentor_id)
        multiplier = QUALITY_MULTIPLIER.get(quality, 1.0)
        gold = int(BASE_REWARD_GOLD * (1 + mentor.graduated_count) * multiplier)
        mentor.graduated_count += 1
        mentor.total_reward_gold += gold
        return {
            "gold": gold,
            "quality": quality,
            "graduated_count": mentor.graduated_count,
            "total_gold": mentor.total_reward_gold,
        }

    def graduate(self, rel_id, quality="normal", now=None):
        rel = self.relations[rel_id]
        if rel.status != "active":
            return None
        rel.status = "graduated"
        rel.ended_at = self._now(now)
        return self.graduate_reward(rel.mentor, quality)

    def update_task(self, rel_id, task, progress, who):
        rel = self.relations[rel_id]
        if rel.status != "active":
            return False
        if who not in (rel.mentor, rel.apprentice):
            return False
        rel.progress[task] = rel.progress.get(task, 0) + progress
        rel.contributors.setdefault(task, set()).add(who)
        return True

    def end_relation(self, rel_id, now=None):
        now = self._now(now)
        rel = self.relations[rel_id]
        if rel.status != "active":
            return None
        rel.status = "ended"
        rel.ended_at = now
        mentor = self._player(rel.mentor)
        apprentice = self._player(rel.apprentice)
        mentor.cooldown_until = now + DISSOLVE_COOLDOWN
        apprentice.cooldown_until = now + DISSOLVE_COOLDOWN
        penalty = int(mentor.total_reward_gold * DISSOLVE_PENALTY_RATE)
        mentor.total_reward_gold -= penalty
        return {
            "cooldown_until": mentor.cooldown_until,
            "penalty_gold": penalty,
            "total_gold": mentor.total_reward_gold,
        }

    def get_apprentice_bonus(self, apprentice_id, in_party=False):
        for rel in self.relations:
            if rel.apprentice == apprentice_id and rel.status == "active":
                bonus = dict(BASE_BONUS)
                if in_party:
                    for key, value in PARTY_BONUS.items():
                        bonus[key] = bonus.get(key, 0) + value
                bonus["in_party"] = in_party
                return bonus
        return {}
