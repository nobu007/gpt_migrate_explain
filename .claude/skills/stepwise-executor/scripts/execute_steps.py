#!/usr/bin/env python3
"""
Step Executor - 中間目標を順次実行

decompose_goal.pyで生成された中間目標を順次実行します。
各ステップの実行状況を記録し、進捗を追跡します。
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# 共通ライブラリパスを追加（.claudeディレクトリを動的に探す）
def find_claude_lib():
    current = Path(__file__).resolve()
    for _ in range(8):  # 最大8階層まで遡る
        claude_lib = current / ".claude" / "lib" / "python"
        if claude_lib.exists():
            return str(claude_lib)
        current = current.parent
        if current == current.parent:  # ファイルシステムルートに到達
            break
    return None  # 見つからない場合


claude_lib_path = find_claude_lib()
if claude_lib_path:
    sys.path.insert(0, claude_lib_path)
    from env_utils import load_env_files, setup_python_path

    # 環境初期化（必須）
    setup_python_path()
    load_env_files()
else:
    import warnings

    warnings.warn("Miyabi共通ライブラリが見つかりませんでした", stacklevel=2)


def load_decomposed_goal(file_path: str) -> dict[str, Any]:
    """
    分解された目標をファイルから読み込む

    Args:
        file_path: 分解結果ファイルのパス

    Returns:
        分解結果
    """
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def initialize_progress(goal: dict[str, Any]) -> dict[str, Any]:
    """
    進捗追跡データを初期化する

    Args:
        goal: 分解された目標

    Returns:
        進捗データ
    """
    return {
        "original_goal": goal["original_goal"],
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "status": "in_progress",
        "total_steps": len(goal["steps"]),
        "completed_steps": 0,
        "steps": [
            {
                "step": step["step"],
                "title": step["title"],
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "notes": [],
            }
            for step in goal["steps"]
        ],
    }


def save_progress(progress: dict[str, Any], output_file: str):
    """
    進捗データを保存する

    Args:
        progress: 進捗データ
        output_file: 出力ファイルパス
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def print_step_header(step: dict[str, Any]):
    """
    ステップのヘッダーを表示する

    Args:
        step: ステップ情報
    """
    print("\n" + "=" * 60)
    print(f"📍 ステップ {step['step']}: {step['title']}")
    print("=" * 60)
    print(f"説明: {step['description']}")
    print(f"推定作業量: {step['estimated_effort']}")
    if step["dependencies"]:
        print(f"依存ステップ: {', '.join(map(str, step['dependencies']))}")
    print()


def execute_step(
    step: dict[str, Any], progress: dict[str, Any], interactive: bool
) -> bool:
    """
    単一のステップを実行する

    Args:
        step: 実行するステップ
        progress: 進捗データ
        interactive: インタラクティブモードかどうか

    Returns:
        実行成功したかどうか
    """
    step_index = step["step"] - 1
    progress_step = progress["steps"][step_index]

    # ステップ開始
    progress_step["status"] = "in_progress"
    progress_step["started_at"] = datetime.now().isoformat()

    print_step_header(step)

    # 実行プロンプトを生成
    execution_prompt = f"""次のステップを実行してください:

タイトル: {step['title']}
説明: {step['description']}
推定作業量: {step['estimated_effort']}

このステップを完了させるために必要な作業を実行してください。
完了したら、実行内容をまとめて報告してください。"""

    print("🤖 Claude Code に以下の指示を送信してください:")
    print("-" * 60)
    print(execution_prompt)
    print("-" * 60)

    if interactive:
        print("\nステップの実行結果を入力してください（空行で終了）:")
        notes = []
        while True:
            line = input()
            if not line:
                break
            notes.append(line)

        progress_step["notes"] = notes

        # ステップ完了確認
        while True:
            response = input("\nこのステップは完了しましたか? (y/n): ").lower()
            if response == "y":
                progress_step["status"] = "completed"
                progress_step["completed_at"] = datetime.now().isoformat()
                progress["completed_steps"] += 1
                print("✅ ステップ完了")
                return True
            if response == "n":
                response = input("このステップをスキップしますか? (y/n): ").lower()
                if response == "y":
                    progress_step["status"] = "skipped"
                    progress_step["completed_at"] = datetime.now().isoformat()
                    print("⏭️  ステップスキップ")
                    return True
                print("ステップを再実行してください")
                return False
    else:
        # 非インタラクティブモード（自動実行）
        print("\n⚠️  非インタラクティブモードでは、手動で各ステップを実行してください")
        print("進捗は track_progress.py で確認できます")
        return True


def execute_all_steps(
    goal: dict[str, Any],
    progress: dict[str, Any],
    interactive: bool,
    progress_file: str,
):
    """
    すべてのステップを順次実行する

    Args:
        goal: 分解された目標
        progress: 進捗データ
        interactive: インタラクティブモードかどうか
        progress_file: 進捗ファイルのパス
    """
    print(f"\n🚀 実行開始: {goal['original_goal']}")
    print(f"総ステップ数: {len(goal['steps'])}")

    for step in goal["steps"]:
        # 依存チェック
        if step["dependencies"]:
            for dep in step["dependencies"]:
                dep_step = progress["steps"][dep - 1]
                if dep_step["status"] != "completed":
                    print(
                        f"\n⚠️  警告: ステップ {step['step']} は ステップ {dep} に依存していますが、"
                        f"ステップ {dep} が未完了です"
                    )
                    if not interactive:
                        continue

        # ステップ実行
        success = execute_step(step, progress, interactive)

        # 進捗保存
        save_progress(progress, progress_file)

        if not success and interactive:
            retry = input("\nステップを再試行しますか? (y/n): ").lower()
            if retry == "y":
                continue
            break

    # 全体の完了チェック
    if progress["completed_steps"] == progress["total_steps"]:
        progress["status"] = "completed"
        progress["completed_at"] = datetime.now().isoformat()
        print("\n🎉 すべてのステップが完了しました！")
    else:
        print(
            f"\n📊 進捗: {progress['completed_steps']}/{progress['total_steps']} ステップ完了"
        )


def main():
    parser = argparse.ArgumentParser(description="分解された中間目標を順次実行します")
    parser.add_argument(
        "goal_file", help="分解結果ファイル（decompose_goal.py の出力）"
    )
    parser.add_argument(
        "-p",
        "--progress",
        default="progress.json",
        help="進捗ファイルのパス（デフォルト: progress.json）",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="インタラクティブモード（各ステップで入力を求める）",
    )
    parser.add_argument(
        "--resume", action="store_true", help="既存の進捗ファイルから再開する"
    )

    args = parser.parse_args()

    # 目標の読み込み
    goal = load_decomposed_goal(args.goal_file)

    # 進捗の初期化または読み込み
    if args.resume and Path(args.progress).exists():
        with open(args.progress, encoding="utf-8") as f:
            progress = json.load(f)
        print(f"📂 既存の進捗を読み込みました: {args.progress}")
    else:
        progress = initialize_progress(goal)
        save_progress(progress, args.progress)
        print(f"📝 進捗ファイルを初期化しました: {args.progress}")

    # ステップ実行
    execute_all_steps(goal, progress, args.interactive, args.progress)

    print(f"\n進捗の詳細: track_progress.py {args.progress}")


if __name__ == "__main__":
    main()
