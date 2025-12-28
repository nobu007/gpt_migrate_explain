#!/usr/bin/env python3
"""/create-issue コマンド実行スクリプト"""

import sys
from pathlib import Path

# スクリプトディレクトリをパスに追加
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from issue_creator import IssueCreator


def main():
    """create-issue コマンドのメイン実行"""
    creator = IssueCreator()

    # コマンドライン引数を処理
    if len(sys.argv) > 1:
        if sys.argv[1] == "--batch" and len(sys.argv) >= 3:
            # バッチモード
            yaml_file = sys.argv[2]
            results = creator.create_batch(yaml_file)
            success_count = sum(1 for r in results if r["success"])
            sys.exit(0 if success_count > 0 else 1)
        else:
            print("❌ 無効な引数です")
            print("使用方法: /create-issue [--batch <yaml_file>]")
            sys.exit(1)
    else:
        # 対話モード
        result = creator.create_interactive()

        # 結果をJSONで出力（Claude Codeとの統合用）
        if not result["success"]:
            print(f"Error: {result['message']}", file=sys.stderr)
            sys.exit(1)
        else:
            # 成功した場合、Issue情報をJSONで出力
            import json

            print(
                json.dumps(
                    {
                        "issue_number": result.get("issue_number"),
                        "issue_url": result.get("issue_url"),
                        "message": result["message"],
                    }
                )
            )
            sys.exit(0)


if __name__ == "__main__":
    main()
