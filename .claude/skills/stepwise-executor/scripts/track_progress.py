#!/usr/bin/env python3
"""
Progress Tracker - 実行進捗の追跡と表示

execute_steps.pyで記録された進捗を読み込み、現在の状況を表示します。
完了したステップ、進行中のステップ、残りのステップを一目で確認できます。
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


def load_progress(file_path: str) -> dict[str, Any]:
    """
    進捗データをファイルから読み込む

    Args:
        file_path: 進捗ファイルのパス

    Returns:
        進捗データ
    """
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def calculate_duration(started_at: str, completed_at: str = None) -> str:
    """
    経過時間を計算する

    Args:
        started_at: 開始時刻（ISO形式）
        completed_at: 完了時刻（ISO形式、オプション）

    Returns:
        経過時間の文字列表現
    """
    start = datetime.fromisoformat(started_at)
    end = datetime.fromisoformat(completed_at) if completed_at else datetime.now()

    duration = end - start
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    seconds = duration.seconds % 60

    if duration.days > 0:
        return f"{duration.days}日 {hours}時間"
    if hours > 0:
        return f"{hours}時間 {minutes}分"
    if minutes > 0:
        return f"{minutes}分 {seconds}秒"
    return f"{seconds}秒"


def get_status_icon(status: str) -> str:
    """
    ステータスに対応するアイコンを取得する

    Args:
        status: ステータス

    Returns:
        アイコン文字列
    """
    icons = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "skipped": "⏭️",
        "failed": "❌",
    }
    return icons.get(status, "❓")


def print_overall_summary(progress: dict[str, Any]):
    """
    全体のサマリーを表示する

    Args:
        progress: 進捗データ
    """
    print("\n" + "=" * 70)
    print("📊 実行進捗サマリー")
    print("=" * 70)

    print(f"\n目標: {progress['original_goal']}")
    print(f"ステータス: {get_status_icon(progress['status'])} {progress['status']}")
    print(f"開始時刻: {progress['started_at']}")

    if progress["completed_at"]:
        print(f"完了時刻: {progress['completed_at']}")
        duration = calculate_duration(progress["started_at"], progress["completed_at"])
        print(f"総実行時間: {duration}")
    else:
        duration = calculate_duration(progress["started_at"])
        print(f"経過時間: {duration}")

    # 進捗率の計算
    completion_rate = (progress["completed_steps"] / progress["total_steps"]) * 100
    print(
        f"\n進捗: {progress['completed_steps']}/{progress['total_steps']} ステップ完了 ({completion_rate:.1f}%)"
    )

    # プログレスバー
    bar_length = 40
    filled = int(bar_length * completion_rate / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"[{bar}]")


def print_steps_detail(progress: dict[str, Any], filter_status: str = None):
    """
    各ステップの詳細を表示する

    Args:
        progress: 進捗データ
        filter_status: フィルタするステータス（オプション）
    """
    print("\n" + "-" * 70)
    print("📋 ステップ詳細")
    print("-" * 70)

    for step in progress["steps"]:
        # フィルタリング
        if filter_status and step["status"] != filter_status:
            continue

        icon = get_status_icon(step["status"])
        print(f"\n{icon} ステップ {step['step']}: {step['title']}")
        print(f"   ステータス: {step['status']}")

        if step["started_at"]:
            print(f"   開始: {step['started_at']}")

        if step["completed_at"]:
            print(f"   完了: {step['completed_at']}")
            duration = calculate_duration(step["started_at"], step["completed_at"])
            print(f"   所要時間: {duration}")

        if step["notes"]:
            print("   メモ:")
            for note in step["notes"]:
                print(f"     - {note}")


def print_next_steps(progress: dict[str, Any]):
    """
    次に実行すべきステップを表示する

    Args:
        progress: 進捗データ
    """
    print("\n" + "-" * 70)
    print("🎯 次のステップ")
    print("-" * 70)

    # 次の未完了ステップを探す
    next_step = None
    for step in progress["steps"]:
        if step["status"] in ["pending", "in_progress"]:
            next_step = step
            break

    if next_step:
        print(f"\nステップ {next_step['step']}: {next_step['title']}")
        print(f"ステータス: {next_step['status']}")
    else:
        print("\n✅ すべてのステップが完了しています！")


def export_report(progress: dict[str, Any], output_file: str):
    """
    進捗レポートをMarkdown形式で出力する

    Args:
        progress: 進捗データ
        output_file: 出力ファイルパス
    """
    lines = []

    # ヘッダー
    lines.append("# 実行進捗レポート\n")
    lines.append(f"**目標**: {progress['original_goal']}\n")
    lines.append(f"**ステータス**: {progress['status']}\n")
    lines.append(f"**開始時刻**: {progress['started_at']}\n")

    if progress["completed_at"]:
        lines.append(f"**完了時刻**: {progress['completed_at']}\n")

    completion_rate = (progress["completed_steps"] / progress["total_steps"]) * 100
    lines.append(
        f"**進捗**: {progress['completed_steps']}/{progress['total_steps']} ({completion_rate:.1f}%)\n"
    )

    # ステップ詳細
    lines.append("\n## ステップ詳細\n")

    for step in progress["steps"]:
        icon = get_status_icon(step["status"])
        lines.append(f"\n### {icon} ステップ {step['step']}: {step['title']}\n")
        lines.append(f"- **ステータス**: {step['status']}\n")

        if step["started_at"]:
            lines.append(f"- **開始**: {step['started_at']}\n")

        if step["completed_at"]:
            lines.append(f"- **完了**: {step['completed_at']}\n")

        if step["notes"]:
            lines.append("\n**メモ**:\n")
            for note in step["notes"]:
                lines.append(f"- {note}\n")

    # ファイル保存
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"\n📄 レポートを出力しました: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="実行進捗を追跡して表示します")
    parser.add_argument("progress_file", help="進捗ファイル（execute_steps.py の出力）")
    parser.add_argument(
        "-f",
        "--filter",
        choices=["pending", "in_progress", "completed", "skipped", "failed"],
        help="特定のステータスのステップのみ表示",
    )
    parser.add_argument(
        "-s",
        "--summary-only",
        action="store_true",
        help="サマリーのみ表示（ステップ詳細を省略）",
    )
    parser.add_argument(
        "-e", "--export", help="レポートをMarkdown形式で出力するファイルパス"
    )

    args = parser.parse_args()

    # 進捗の読み込み
    try:
        progress = load_progress(args.progress_file)
    except FileNotFoundError:
        print(f"Error: 進捗ファイルが見つかりません: {args.progress_file}")
        sys.exit(1)

    # サマリー表示
    print_overall_summary(progress)

    # ステップ詳細表示
    if not args.summary_only:
        print_steps_detail(progress, args.filter)
        print_next_steps(progress)

    # レポート出力
    if args.export:
        export_report(progress, args.export)


if __name__ == "__main__":
    main()
