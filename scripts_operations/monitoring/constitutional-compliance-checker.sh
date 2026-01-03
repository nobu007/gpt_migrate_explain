#!/bin/bash
# 憲法コンプライアンスチェックスクリプト - Python実装のラッパー
# 高度な.module検証機能を提供するconstitutional-compliance-checker.pyを呼び出し

# Python版の憲法コンプライアンスチェッカーを実行
python3 "$(dirname "$0")/constitutional-compliance-checker.py" "$@"

# Pythonスクリプトの終了コードをそのまま返す
exit $?