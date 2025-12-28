---
description: 統合审批屏幕 - QA、Deploy、PR、CodeReviewなど
---

# Approve Command - 統合审批屏幕

承認が必要な操作のための統合UI画面を提供します。

## 使用方法

```bash
/approve [type] [id]
```

## パラメータ

- `type` (必須): 承認タイプ
  - `qa`: QAレビュー承認
  - `deploy`: デプロイ承認
  - `pr`: プルリクエスト承認
  - `code-review`: コードレビュー承認
  - `hotfix`: ホットフィックス承認
  - `release`: リリース承認

- `id` (オプション): 承認対象ID（省略時はリスト表示）

## 実行内容

### 1. 承認画面の起動

```typescript
// Reactコンポーネントで承認画面を起動
const approvalScreen = await ApprovalScreen.launch({
  type: 'deploy',
  id: 'deploy-123'
});
```

### 2. 承認タイプ別のUI

#### QA承認画面
```typescript
interface QAApprovalData {
  id: string;
  title: string;
  description: string;
  testResults: TestResult[];
  coverage: number;
  criticalIssues: number;
  reviewer: string;
  status: 'pending' | 'approved' | 'rejected';
  createdAt: Date;
  deadline?: Date;
}
```

#### デプロイ承認画面
```typescript
interface DeployApprovalData {
  id: string;
  environment: 'staging' | 'production';
  version: string;
  changes: Change[];
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  approvals: Approval[];
  checklist: ChecklistItem[];
  rollbackPlan: string;
  estimatedDowntime: number;
}
```

#### PR承認画面
```typescript
interface PRApprovalData {
  id: string;
  title: string;
  description: string;
  author: string;
  reviewers: Reviewer[];
  changes: FileChange[];
  conflicts: Conflict[];
  checks: StatusCheck[];
  discussion: Comment[];
  mergeable: boolean;
}
```

### 3. 承認フロー

```mermaid
graph TD
    A[/approve実行] --> B{タイプ指定}
    B -->|qa| C[QA承認画面]
    B -->|deploy| D[デプロイ承認画面]
    B -->|pr| E[PR承認画面]
    B -->|省略| F[承認待ちリスト]

    C --> G[詳細情報表示]
    D --> H[リスク評価表示]
    E --> I[変更内容表示]

    G --> J[承認/拒否選択]
    H --> J
    I --> J

    J -->|承認| K[承認処理実行]
    J -->|拒否| L[拒否理由入力]
    J -->|保留| M[コメント追加]

    K --> N[結果通知]
    L --> N
    M --> N
```

## UIコンポーネント構成

### メイン承認画面
```typescript
// src/components/approval/ApprovalScreen.tsx
interface ApprovalScreenProps {
  type: ApprovalType;
  data?: ApprovalData;
  onApprove?: (data: ApprovalData) => Promise<void>;
  onReject?: (data: ApprovalData, reason: string) => Promise<void>;
  onComment?: (data: ApprovalData, comment: string) => Promise<void>;
}
```

### 共通UI要素
- **StatusBadge**: 状態表示（Pending, Approved, Rejected）
- **RiskIndicator**: リスクレベル表示
- **ApproverAvatar**: 承認者アバター
- **Timeline**: 承認履歴タイムライン
- **CommentSection**: コメントセクション
- **Checklist**: チェックリスト

### レスポンシブデザイン
```typescript
// モバイル対応
const MobileApprovalView = () => (
  <div className="lg:hidden">
    {/* モバイル用コンパクト表示 */}
  </div>
);

// デスクトップ表示
const DesktopApprovalView = () => (
  <div className="hidden lg:block">
    {/* デスクトップ用詳細表示 */}
  </div>
);
```

## 承認ロジック

### 1. 承認権限チェック
```python
# src/core/approval/permissions.py
class ApprovalPermissionChecker:
    def can_approve(self, user: User, approval_type: str, data: dict) -> bool:
        # ユーザーの権限をチェック
        # 必要なロールを持っているか確認
        # 利益相反チェック
        pass
```

### 2. 承認処理実行
```python
# src/core/approval/processor.py
class ApprovalProcessor:
    async def process_approval(self, approval_id: str, action: str, user: User, comment: str = None):
        # データベース更新
        # 通知送信
        # 後続処理トリガー
        # ログ記録
        pass
```

### 3. 承認後のアクション
```python
# 承認タイプ別の後続処理
ACTIONS = {
    'qa': 'trigger_deployment_pipeline',
    'deploy': 'execute_deployment',
    'pr': 'merge_pull_request',
    'hotfix': 'apply_hotfix',
    'release': 'publish_release'
}
```

## 承認リスト表示

### ダッシュボード機能
```typescript
// 未処理の承認リスト
const PendingApprovals = () => {
  const [approvals, setApprovals] = useState<ApprovalSummary[]>([]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {approvals.map(approval => (
        <ApprovalCard
          key={approval.id}
          approval={approval}
          onClick={() => navigate(`/approve/${approval.type}/${approval.id}`)}
        />
      ))}
    </div>
  );
};
```

### フィルタリング機能
```typescript
// 承認のフィルタリングと検索
const ApprovalFilters = () => {
  return (
    <div className="flex flex-wrap gap-2 mb-6">
      <Select placeholder="タイプを選択" options={approvalTypes} />
      <Select placeholder="ステータスを選択" options={statusOptions} />
      <Select placeholder="優先度を選択" options={priorityOptions} />
      <Input placeholder="検索..." leftIcon={<SearchIcon />} />
    </div>
  );
};
```

## 通知システム

### 1. 承認要求通知
```python
# Slack通知
async def send_approval_request_notification(approval: Approval):
    message = {
        "text": f"承認要求: {approval.title}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{approval.title}*\n{approval.description}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "承認"},
                        "url": f"{BASE_URL}/approve/{approval.type}/{approval.id}"
                    }
                ]
            }
        ]
    }
    await send_slack_notification(message)
```

### 2. 承認完了通知
```python
# 承認者へのフィードバック
async def send_approval_completion_notification(approval: Approval, action: str):
    # 承認者に通知
    # 要求者に通知
    # 関連チームに通知
    pass
```

## セキュリティ機能

### 1. 二要素認証
```typescript
// 高リスク承認には2FA必須
const TwoFactorAuth = ({ required, onVerify }) => {
  const [code, setCode] = useState('');

  const handleVerify = async () => {
    const verified = await verify2FACode(code);
    if (verified) {
      onVerify();
    }
  };

  return required ? (
    <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <h4 className="text-sm font-medium text-yellow-800 mb-2">
        二要素認証が必要です
      </h4>
      <Input
        placeholder="認証コードを入力"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        maxLength={6}
      />
      <Button onClick={handleVerify} className="mt-2">認証</Button>
    </div>
  ) : null;
};
```

### 2. 承認履歴の追跡
```python
# 監査証跡
class ApprovalAuditLogger:
    def log_approval_action(self, approval_id: str, user: User, action: str,
                          timestamp: datetime, ip_address: str, user_agent: str):
        audit_log = {
            "approval_id": approval_id,
            "user_id": user.id,
            "action": action,
            "timestamp": timestamp.isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "session_id": user.session_id
        }
        self.save_audit_log(audit_log)
```

## 統合機能

### 1. 既存システムとの連携
```python
# QAシステム連携
class QAApprovalIntegration:
    def sync_qa_results(self, approval_id: str):
        # QAシステムからテスト結果を取得
        # 承認画面に表示
        pass

# CI/CD連携
class DeployApprovalIntegration:
    def trigger_deployment(self, approval_id: str):
        # 承認後にデプロイパイプラインを起動
        pass
```

### 2. APIエンドポイント
```python
# FastAPIエンドポイント
@app.post("/api/approvals/{approval_id}/approve")
async def approve_approval(
    approval_id: str,
    approval_data: ApprovalRequest,
    current_user: User = Depends(get_current_user)
):
    # 承認処理
    pass

@app.post("/api/approvals/{approval_id}/reject")
async def reject_approval(
    approval_id: str,
    rejection_data: RejectionRequest,
    current_user: User = Depends(get_current_user)
):
    # 拒否処理
    pass
```

## 実行例

### QA承認
```bash
/approve qa qa-2024-001

# 期待されるUI:
# ┌─────────────────────────────────────┐
# │ QA承認: v2.1.0 リリーステスト      │
# ├─────────────────────────────────────┤
# │ テストカバレッジ: 92% ✅           │
# │ クリティカル問題: 0件 ✅           │
# │ レビュアー: 山田太郎               │
# │                                     │
# │ [詳細を表示] [承認] [拒否]          │
# └─────────────────────────────────────┘
```

### デプロイ承認
```bash
/approve deploy deploy-123

# 期待されるUI:
# ┌─────────────────────────────────────┐
# │ 本番環境デプロイ承認                │
# │ バージョン: v1.2.3                 │
# │ リスクレベル: 高🔴                 │
# │                                     │
# │ ✓ テスト完了                        │
# │ ✓ ロールバック計画                  │
# │ ⚠ データベース移行を含む           │
# │                                     │
# │ [変更確認] [承認] [拒否]            │
# └─────────────────────────────────────┘
```

### 承認リスト
```bash
/approve

# 期待されるUI:
# ┌─────────────────────────────────────┐
# │ 承認待ち (3件)                      │
# ├─────────────────────────────────────┤
# │ 🔴 高優先度                         │
# │ • 本番デプロイ (deploy-123)         │
# │ • ホットフィックス (hotfix-456)     │
# │                                     │
# │ 🟡 中優先度                         │
# │ • PRレビュー (pr-789)               │
# │                                     │
# │ [全て表示]                          │
# └─────────────────────────────────────┘
```

## 設定

### 環境変数
```bash
# .env
APPROVAL_WEBHOOK_URL=https://hooks.slack.com/...
APPROVAL_2FA_REQUIRED=true
APPROVAL_MAX_PENDING_DAYS=7
APPROVAL_AUTO_REMINDER_HOURS=24
```

### 承認ポリシー設定
```yaml
# approval_config.yml
approval_policies:
  deploy:
    required_approvers: 2
    risk_assessment: true
    two_factor_auth: true

  qa:
    required_approvers: 1
    minimum_coverage: 80
    critical_issues_threshold: 0

  pr:
    required_approvers: 2
    auto_merge: false
    conflict_check: true
```

## 拡張機能

### 1. 承認テンプレート
```typescript
// 承認依頼テンプレート
const approvalTemplates = {
  deploy: {
    title: "デプロイ承認依頼",
    description: "バージョン {version} を {environment} 環境にデプロイします",
    checklist: [
      "テストが完了している",
      "ロールバック計画が準備されている",
      "メンテナンスウィンドウが確保されている"
    ]
  }
};
```

### 2. 自動承認ルール
```python
# 特定条件下で自動承認
class AutoApprovalRules:
    def should_auto_approve(self, approval: Approval) -> bool:
        # 低リスク変更
        # 信頼済み担当者
        # テスト合格
        # 自動承認条件をチェック
        pass
```

### 3. 承認 analytics
```python
# 承認パフォーマンス分析
class ApprovalAnalytics:
    def generate_metrics(self) -> ApprovalMetrics:
        # 平均承認時間
        # 承認率
        # ボトルネック分析
        # 改善提案
        pass
```

## トラブルシューティング

### Q1: 承認画面が表示されない
```bash
# 必要なモジュールを確認
ls src/components/approval/
npm list @types/react
```

### Q2: 承認権限がない
```bash
# ユーザーロールを確認
python scripts_python/check_permissions.py --user=$(whoami)
```

### Q3: 通知が届かない
```bash
# Webhook設定を確認
curl -X POST $APPROVAL_WEBHOOK_URL -d '{"text":"test"}'
```

## 関連ドキュメント

- [DEPLOY.md](../../DEPLOYMENT.md) - デプロイ手順
- [qa_review.md](../../docs/QA_REVIEW_GUIDELINES.md) - QAレビュー基準
- [src/components/approval/](../../src/computer_use_web/src/components/approval/) - UIコンポーネント
- [src/core/approval/](../../src/core/approval/) - バックエンドロジック

---

🤖 このコマンドは統合审批システムによって管理されます。
