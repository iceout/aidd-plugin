"""基础运行时测试"""

import os
from pathlib import Path

import pytest
from aidd_runtime import runtime
from aidd_runtime.feature_ids import FeatureIdentifiers, read_active_state
from aidd_runtime.stage_lexicon import resolve_stage_name


class TestBasicRuntime:
    """测试基础运行时功能"""

    def test_require_plugin_root_with_env(self, monkeypatch):
        """测试 AIDD_ROOT 环境变量"""
        monkeypatch.setenv("AIDD_ROOT", "/tmp/test-aidd")
        root = runtime.require_plugin_root()
        # macOS 可能会解析 /tmp 为 /private/tmp
        assert "/tmp/test-aidd" in str(root)

    def test_require_plugin_root_missing(self, monkeypatch):
        """测试缺少环境变量时抛出异常"""
        monkeypatch.delenv("AIDD_ROOT", raising=False)

        with pytest.raises(RuntimeError, match="AIDD_ROOT"):
            runtime.require_plugin_root()

    def test_feature_identifiers(self):
        """测试功能标识符"""
        fid = FeatureIdentifiers(ticket="TEST-123", slug_hint="test-feature")
        assert fid.resolved_ticket == "TEST-123"
        assert fid.has_hint is True

        # 测试没有 hint
        fid2 = FeatureIdentifiers(ticket="TEST-456")
        assert fid2.has_hint is False

    def test_stage_lexicon(self):
        """测试阶段词汇表"""
        assert resolve_stage_name("idea") == "idea"
        assert resolve_stage_name("research") == "research"
        # 注意：别名需要检查 stage_lexicon.py 中是否定义
        # resolve_stage_name 返回标准阶段名

    def test_active_state_file_not_found(self, tmp_path):
        """测试读取不存在的 active state"""
        state = read_active_state(tmp_path)
        assert state.ticket is None
        assert state.stage is None


class TestRuntimePaths:
    """测试路径解析"""

    def test_rel_path(self):
        """测试相对路径计算"""
        root = Path("/home/user/project/aidd")
        path = Path("/home/user/project/aidd/docs/test.md")
        result = runtime.rel_path(path, root)
        assert result == "aidd/docs/test.md"

    def test_is_relative_to(self):
        """测试路径相对性检查"""
        path = Path("/a/b/c")
        ancestor = Path("/a/b")
        assert runtime.is_relative_to(path, ancestor) is True

        not_ancestor = Path("/x/y")
        assert runtime.is_relative_to(path, not_ancestor) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
