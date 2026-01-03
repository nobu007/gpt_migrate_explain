#!/bin/bash

# GitHub Issue Monitor 実行スクリプト
# CI/CDパイプライン監視とGitHub Issue改善機能を統合して実行

set -euo pipefail

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Pythonパスを設定
export PYTHONPATH="$PROJECT_ROOT/src:$PROJECT_ROOT:$PYTHONPATH"

# 色付け関数
color_red() { echo -e "\033[31m$*\033[0m"; }
color_green() { echo -e "\033[32m$*\033[0m"; }
color_yellow() { echo -e "\033[33m$*\033[0m"; }
color_blue() { echo -e "\033[34m$*\033[0m"; }

# ヘルプ表示
show_help() {
    cat << EOF
GitHub Issue Monitor 実行スクリプト

使用法:
    $0 [MODE] [OPTIONS]

モード:
    integrated   統合監視モード - パイプライン監視 + Issue改善
    periodic     周期実行モード - 定期的なIssue改善
    status       ステータス確認 - 監視状況の確認
    test         テスト実行 - 機能テスト

オプション (integratedモード):
    --health-percentage NUM  パイプライン健康度パーセンテージ
    --health-status TEXT     健康度ステータス
    --total-score NUM        合計スコア
    --max-score NUM          最大スコア
    --duration NUM           実行時間（秒）
    --pipeline-mode TEXT     パイプラインモード
    --threshold NUM          Issue作成閾値（デフォルト: 50）

オプション (periodicモード):
    --interval NUM           実行間隔（時間、デフォルト: 24）
    --cycles NUM             最大サイクル数（0=無限）

環境変数:
    GITHUB_TOKEN             GitHub APIトークン（必須）
    GITHUB_REPOSITORY_OWNER  リポジトリオーナー（デフォルト: nobu007）
    GITHUB_REPOSITORY_NAME   リポジトリ名（デフォルト: ucg-devops）

例:
    # CI/CD統合監視
    $0 integrated \\
        --health-percentage 45 \\
        --health-status "warning" \\
        --total-score 22 \\
        --max-score 50 \\
        --duration 900 \\
        --pipeline-mode "full"

    # 1時間ごとに5サイクル実行
    $0 periodic --interval 1 --cycles 5

    # ステータス確認
    $0 status

    # テスト実行
    $0 test

EOF
}

# 環境チェック
check_environment() {
    echo "$(color_blue "=== 環境チェック ===")"

    # Pythonチェック
    if ! command -v python3 &> /dev/null; then
        echo "$(color_red "エラー: python3 が見つかりません")"
        exit 1
    fi

    # 必要な環境変数チェック
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        echo "$(color_yellow "警告: GITHUB_TOKEN が設定されていません")"
        echo "GitHub API操作にはトークンが必要です"
    fi

    # プロジェクト構造チェック
    if [[ ! -f "$PROJECT_ROOT/scripts_operations/monitoring/github_issue_monitor_integration.py" ]]; then
        echo "$(color_red "エラー: 統合監視スクリプトが見つかりません")"
        exit 1
    fi

    echo "$(color_green "✅ 環境チェック完了")"
    echo
}

# 統合監視実行
run_integrated() {
    echo "$(color_blue "=== GitHub Issue 統合監視開始 ===")"

    cd "$PROJECT_ROOT"
    python3 scripts_operations/monitoring/github_issue_monitor_integration.py "$@"
}

# 周期実行
run_periodic() {
    echo "$(color_blue "=== GitHub Issue 周期監視開始 ===")"

    cd "$PROJECT_ROOT"
    python3 scripts_operations/monitoring/github_issue_monitor_integration.py "$@"
}

# ステータス確認
show_status() {
    echo "$(color_blue "=== GitHub Issue 監視ステータス ===")"

    cd "$PROJECT_ROOT"
    python3 scripts_operations/monitoring/github_issue_monitor_integration.py --mode status
}

# テスト実行
run_tests() {
    echo "$(color_blue "=== GitHub Issue 機能テスト ===")"

    cd "$PROJECT_ROOT"

    # Issue Improverテスト
    if [[ -f "test_issue_improver.py" ]]; then
        echo "$(color_yellow "Issue Improver テスト実行中...")"
        python3 test_issue_improver.py
        echo
    fi

    # 統合システムテスト
    if [[ -f "test_integration.py" ]]; then
        echo "$(color_yellow "統合システムテスト実行中...")"
        python3 test_integration.py
        echo
    fi

    echo "$(color_green "✅ すべてのテスト完了")"
}

# メイン処理
main() {
    # 引数がない場合はヘルプを表示
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi

    # モードを取得
    MODE="$1"
    shift

    case "$MODE" in
        "integrated")
            check_environment
            run_integrated --mode integrated "$@"
            ;;
        "periodic")
            check_environment
            run_periodic --mode periodic "$@"
            ;;
        "status")
            show_status
            ;;
        "test")
            run_tests
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "$(color_red "エラー: 不正なモード '$MODE'")"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 実行
main "$@"