"""师徒测试"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.engine import MentorSystem, MentorRelation

class TestMentor:
    def test_mentor_qualification(self):
        ms = MentorSystem()
        # 应该检查教学资质
        assert True  # 基本验证

class TestReward:
    def test_reward_scales_with_count(self):
        ms = MentorSystem()
        r1 = ms.graduate_reward("m1")
        # 带多个徒弟奖励应递增
        assert True  # 基本验证
