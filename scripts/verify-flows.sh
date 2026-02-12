#!/bin/bash
# 验证 Flow Skills 是否正确安装

echo "=== AIDD Flow Skills 验证 ==="
echo ""

echo "已安装的 Flow Skills:"
ls ~/.config/agents/skills/ | grep "-flow$" | sed 's/^/  ✓ /'

echo ""
echo "SKILL.md 文件大小:"
for skill in ~/.config/agents/skills/*-flow/; do
  name=$(basename "$skill")
  size=$(stat -f%z "$skill/SKILL.md" 2>/dev/null || echo "0")
  if [ "$size" -gt 0 ]; then
    echo "  ✓ $name: $size bytes"
  else
    echo "  ✗ $name: EMPTY!"
  fi
done

echo ""
echo "Mermaid 图表检查:"
for skill in ~/.config/agents/skills/*-flow/SKILL.md; do
  name=$(basename $(dirname "$skill"))
  has_begin=$(grep -c "BEGIN" "$skill" || echo "0")
  has_end=$(grep -c "END" "$skill" || echo "0")
  if [ "$has_begin" -gt 0 ] && [ "$has_end" -gt 0 ]; then
    echo "  ✓ $name: has BEGIN/END"
  else
    echo "  ✗ $name: missing BEGIN or END"
  fi
done

echo ""
echo "======================="
echo "提示: 如果 Kimi 中仍看不到所有 /flow: 命令，请:"
echo "1. 完全退出 Kimi (Cmd+Q)"
echo "2. 重新启动 Kimi"
echo "3. 输入 / 查看可用命令"
echo "======================="
