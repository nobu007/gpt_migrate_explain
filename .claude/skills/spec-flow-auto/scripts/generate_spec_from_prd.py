#!/usr/bin/env python3
"""
Spec Workflow - PRDからSPECを自動生成するスクリプト

README.mdやPRDドキュメントから、SpecWorkflowMcp準拠の
requirements.md, design.md, tasks.mdを自動生成する
"""

import argparse
import re
import sys
from pathlib import Path


class PRDToSpecGenerator:
    def __init__(self, input_path: str, output_path: str, spec_name: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.spec_name = spec_name
        self.spec_dir = self.output_path / spec_name

    def parse_prd(self) -> dict:
        """PRDドキュメントを解析して構造化データを抽出"""
        content = self.input_path.read_text(encoding="utf-8")

        # 基本セクションの抽出
        sections = {}

        # 見出しを抽出
        re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)
        current_section = None
        current_content = []

        for line in content.split("\n"):
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = heading_match[2]
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def generate_requirements_md(self, sections: dict) -> str:
        """requirements.mdを生成"""
        return f"""# {self.spec_name} Requirements

## Overview

{sections.get('Overview', sections.get('概要', 'このプロジェクトの概要'))}

## Functional Requirements

### FR-001: Core Functionality
{self._extract_functional_requirements(sections)}

### FR-002: User Interface
{self._extract_ui_requirements(sections)}

### FR-003: Data Management
{self._extract_data_requirements(sections)}

## Non-Functional Requirements

### Performance Requirements
- レスポンスタイム: 2秒以内
- 同時接続ユーザー数: 1000人以上
- データ処理量: 1GB/分

### Security Requirements
- 認証・認可機能の実装
- データ暗号化（TLS 1.3）
- 監査ログの記録

### Compatibility Requirements
- ブラウザ対応: Chrome, Firefox, Safari最新版
- OS対応: Windows 10+, macOS 10.15+, Ubuntu 18.04+

## Constraints and Assumptions

### Technical Constraints
- 使用言語: TypeScript, Python
- フレームワーク: React, FastAPI
- データベース: PostgreSQL

### Business Constraints
- 開発期間: 3ヶ月
- 予算制約: 既存インフラの活用
- チーム構成: 5名

## Acceptance Criteria

各機能要件に対する受け入れ基準を以下に定義：

1. **基本機能**: ユーザーが主要な操作を完了できること
2. **UI/UX**: 直感的な操作でタスクを達成できること
3. **性能**: 期待される応答時間内で処理完了すること
4. **セキュリティ**: 脆弱性診断で高危険度の問題がないこと
"""

    def generate_design_md(self, sections: dict) -> str:
        """design.mdを生成"""
        return f"""# {self.spec_name} Design

## Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack
- **Frontend**: React 18+, TypeScript Vite
- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL 15+
- **Infrastructure**: Docker, AWS/Azure

## Component Design

### Frontend Components
- **AuthModule**: 認証関連機能
- **Dashboard**: メインダッシュボード
- **DataManagement**: データ管理機能

### Backend Services
- **AuthService**: 認証サービス
- **DataService**: データ処理サービス
- **APIService**: APIゲートウェイ

## Database Design

### Entity Relationship
主要なエンティティとリレーションシップ：

1. **Users**: ユーザー情報
2. **Roles**: 権限管理
3. **Data**: 主要ビジネスデータ
4. **AuditLogs**: 監査ログ

### Schema Design
```sql
-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roles Table
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    permissions JSONB
);
```

## API Design

### RESTful API Endpoints
```
GET    /api/v1/users           - ユーザー一覧取得
POST   /api/v1/users           - ユーザー作成
GET    /api/v1/users/{{id}}      - ユーザー詳細取得
PUT    /api/v1/users/{{id}}      - ユーザー更新
DELETE /api/v1/users/{{id}}      - ユーザー削除
```

### Authentication
- JWTベースの認証方式
- トークン有効期間: 24時間
- リフレッシュトークン対応

## Security Design

### Authentication & Authorization
- OAuth 2.0 + OpenID Connect
- RBAC（Role-Based Access Control）
- Multi-factor Authentication対応

### Data Protection
- 機密データのAES-256暗号化
- 通信のTLS 1.3化
- 定期的な脆弱性スキャン

## Development Standards

### Coding Standards
- TypeScript: strict mode
- Python: PEP 8準拠
- ESLint + Prettier for code formatting

### Testing Strategy
- 単体テストカバレッジ: 80%以上
- 結合テスト: 主要ユースケースを網羅
- E2Eテスト: クリティカルパスを検証

## Deployment Architecture

### Container Strategy
```dockerfile
# Frontend
FROM node:18-alpine
# React build configuration

# Backend
FROM python:3.11-slim
# FastAPI application setup
```

### CI/CD Pipeline
1. **Code Quality**: ESLint, Security Scan
2. **Testing**: Unit, Integration, E2E
3. **Build**: Docker image creation
4. **Deploy**: Automated deployment to staging/production
"""

    def generate_tasks_md(self, sections: dict) -> str:
        """tasks.mdを生成"""
        return f"""# {self.spec_name} Implementation Tasks

## Task Breakdown

### Phase 1: Foundation Setup
- [ ] 1.1 Repository initialization and CI/CD setup
- [ ] 1.2 Development environment configuration
- [ ] 1.3 Database schema design and migration
- [ ] 1.4 Basic project structure creation

### Phase 2: Backend Development
- [ ] 2.1 User authentication system implementation
- [ ] 2.2 Core API endpoints development
- [ ] 2.3 Database models and services
- [ ] 2.4 Security middleware implementation

### Phase 3: Frontend Development
- [ ] 3.1 React application setup
- [ ] 3.2 Authentication components
- [ ] 3.3 Dashboard implementation
- [ ] 3.4 Data management interface

### Phase 4: Integration & Testing
- [ ] 4.1 Backend-Frontend integration
- [ ] 4.2 API testing and validation
- [ ] 4.3 End-to-end testing scenarios
- [ ] 4.4 Performance optimization

### Phase 5: Deployment & Monitoring
- [ ] 5.1 Production environment setup
- [ ] 5.2 Deployment pipeline configuration
- [ ] 5.3 Monitoring and logging setup
- [ ] 5.4 Documentation and training

## Task Details

### 1.1 Repository initialization and CI/CD setup
**Description**: Gitリポジトリの初期化とCI/CDパイプラインの構築
**Estimated Effort**: 1 day
**Dependencies**: None
**Acceptance Criteria**:
- [ ] GitHub repository created
- [ ] GitHub Actions workflow configured
- [ ] Code quality checks implemented
- [ ] Automated testing pipeline set up

### 2.1 User authentication system implementation
**Description**: JWTベースの認証システムの実装
**Estimated Effort**: 3 days
**Dependencies**: 1.3, 1.4
**Acceptance Criteria**:
- [ ] User registration functionality
- [ ] Login/logout functionality
- [ ] JWT token generation and validation
- [ ] Password reset functionality

### 3.1 React application setup
**Description**: Reactアプリケーションの初期セットアップ
**Estimated Effort**: 2 days
**Dependencies**: 2.1
**Acceptance Criteria**:
- [ ] React + TypeScript project created
- [ ] Routing configured
- [ ] Basic layout structure
- [ ] Development environment verified

## Dependencies

```mermaid
graph TD
    A[1.1 Repository Setup] --> B[1.2 Environment Config]
    A --> C[1.3 Database Design]
    A --> D[1.4 Project Structure]

    B --> E[2.1 Authentication]
    C --> E
    D --> E

    E --> F[2.2 API Development]
    E --> G[2.3 Database Models]
    E --> H[2.4 Security]

    F --> I[3.1 React Setup]
    G --> I
    H --> I

    I --> J[3.2 Auth Components]
    I --> K[3.3 Dashboard]
    I --> L[3.4 Data Interface]

    J --> M[4.1 Integration]
    K --> M
    L --> M
```

## Timeline

| Week | Tasks |
|------|-------|
| Week 1 | Phase 1: Foundation (1.1-1.4) |
| Week 2-3 | Phase 2: Backend (2.1-2.4) |
| Week 3-4 | Phase 3: Frontend (3.1-3.4) |
| Week 5 | Phase 4: Integration (4.1-4.4) |
| Week 6 | Phase 5: Deployment (5.1-5.4) |

## Risk Assessment

### High Risk Items
- **Database Performance**: 大量データ処理時のパフォーマンス
- **Security Implementation**: 認証認可の網羅性
- **Third-party Integrations**: 外部APIとの連携

### Mitigation Strategies
- 早期のパフォーマンステスト実施
- セキュリティ専門家によるレビュー
- 外部APIモックでの事前検証
"""

    def _extract_functional_requirements(self, sections: dict) -> str:
        """機能要件を抽出"""
        # セクションから機能要件に関連する内容を抽出
        for section_name, content in sections.items():
            if any(
                keyword in section_name.lower()
                for keyword in ["機能", "feature", "requirement"]
            ):
                return content[:500] + "..." if len(content) > 500 else content

        return "主要な機能要件をここに記載"

    def _extract_ui_requirements(self, sections: dict) -> str:
        """UI要件を抽出"""
        for section_name, content in sections.items():
            if any(
                keyword in section_name.lower()
                for keyword in ["ui", "interface", "画面"]
            ):
                return content[:300] + "..." if len(content) > 300 else content

        return "ユーザーインターフェース要件をここに記載"

    def _extract_data_requirements(self, sections: dict) -> str:
        """データ要件を抽出"""
        for section_name, content in sections.items():
            if any(
                keyword in section_name.lower()
                for keyword in ["data", "database", "データ"]
            ):
                return content[:300] + "..." if len(content) > 300 else content

        return "データ管理要件をここに記載"

    def generate_spec(self) -> None:
        """SPEC一式を生成"""
        # 出力ディレクトリ作成
        self.spec_dir.mkdir(parents=True, exist_ok=True)

        # PRD解析
        sections = self.parse_prd()

        # 各ドキュメント生成
        requirements = self.generate_requirements_md(sections)
        design = self.generate_design_md(sections)
        tasks = self.generate_tasks_md(sections)

        # ファイル書き込み
        (self.spec_dir / "requirements.md").write_text(requirements, encoding="utf-8")
        (self.spec_dir / "design.md").write_text(design, encoding="utf-8")
        (self.spec_dir / "tasks.md").write_text(tasks, encoding="utf-8")

        print(f"✅ Generated SPEC files for '{self.spec_name}':")
        print(f"   📁 {self.spec_dir}")
        print("   📄 requirements.md")
        print("   📄 design.md")
        print("   📄 tasks.md")


def main():
    parser = argparse.ArgumentParser(description="Generate SPEC from PRD document")
    parser.add_argument("--input", required=True, help="Path to PRD document")
    parser.add_argument("--output", required=True, help="Output directory path")
    parser.add_argument("--spec-name", required=True, help="Specification name")

    args = parser.parse_args()

    # 入力ファイル確認
    if not Path(args.input).exists():
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)

    try:
        generator = PRDToSpecGenerator(args.input, args.output, args.spec_name)
        generator.generate_spec()

    except Exception as e:
        print(f"❌ Error generating SPEC: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
