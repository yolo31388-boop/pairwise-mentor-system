"""师徒系统 - 带5个bug"""
from dataclasses import dataclass, field

@dataclass
class MentorRelation:
    mentor: str
    apprentice: str
    progress: dict
    status: str = "active"

class MentorSystem:
    def __init__(self):
        self.relations: list[MentorRelation] = []
        self.mentor_rating = {}

    def can_mentor(self, mentor_id, apprentice_id):
        # bug1: 只看等级差
        return True

    def start_apprenticeship(self, mentor, apprentice):
        rel = MentorRelation(mentor, apprentice, {})
        self.relations.append(rel)
        return rel

    def graduate_reward(self, mentor_id):
        # bug2: 固定奖励
        return {"gold": 1000}

    def update_task(self, rel_id, task, progress, who):
        rel = self.relations[rel_id]
        # bug3: 进度不共享
        rel.progress[task] = progress
        return True

    def end_relation(self, rel_id):
        # bug4: 无冷却
        self.relations[rel_id].status = "ended"
        return True

    def get_apprentice_bonus(self, apprentice_id):
        # bug5: 只组队生效
        for rel in self.relations:
            if rel.apprentice == apprentice_id and rel.status == "active":
                return {"in_party": True}
        return {}
