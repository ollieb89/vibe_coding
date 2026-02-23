---
title: SuperClaude MCP サーバーガイド 🔌
source: docs/User-Guide-jp/mcp-servers.md
---

# MCP Servers

MCP (Multi-Context Processing) サーバーは、SuperClaude で使用可能な複数の AI モデルを含みます。これらのモデルは、アプリケーション開発、分析、およびエンタープライズリファクタリングに役立ちます。

## サーバーの説明

### Context7

Context7 は、アプリケーション開発を支援する AI モデルです。これは、開発者が使用可能なパターンとベストプラクティスについて教えます。

### Sequential Thinking

Sequential Thinking は、分析を行う AI モデルです。これは、アプリケーションの詳細な分析を行い、問題を解決するために使用できます。

### Magic

Magic は、UI 開発を支援する AI モデルです。これは、ユーザーインターフェイスの高品質なコンポーネントを生成します。

### Playwright

Playwright は、エンドツーエンドテストを行う AI モデルです。これは、Web アプリケーションのテストを自動化するために使用できます。

### Serena

Serena は、永続性を保つために使用される AI モデルです。これは、ワークフローを管理し、アプリケーションの整合性を確保します。

### Morphllm

Morphllm は、大規模なリファクタリングを行う AI モデルです。これは、複数のコードファイルを自動的に整理し、アプリケーションのパフォーマンスを向上させます。

## サーバーの組み合わせ

### APIキーなし（無料）

- コンテキスト7 + シーケンシャルシンキング + 劇作家 + セレナ

### 1 APIキー

- プロフェッショナルなUI開発に魔法を加える

### 2つのAPIキー

- 大規模リファクタリングのために morphllm-fast-apply を追加

### 一般的なワークフロー

- **学習**：コンテキスト7 + シーケンシャルシンキング
- **Web開発**：マジック + context7 + プレイライト
- **エンタープライズリファクタリング**：serena + morphllm + sequential-thinking
- **複雑な分析**：シーケンシャルシンキング + コンテキスト7 + セレナ

## 統合

### SuperClaude コマンドを使用する場合:

- 分析コマンドは自動的にSequential + Serenaを使用します
- 実装コマンドはMagic + Context7を使用する
- テストコマンドにはPlaywright + Sequentialを使用する

### 動作モードの場合:

- ブレインストーミングモード：発見のためのシーケンシャル
- タスク管理：永続性のための Serena
- オーケストレーションモード: 最適なサーバーの選択

### パフォーマンスコントロール:

- システム負荷に基づく自動リソース管理
- 同時実行制御: `--concurrency N`(1-15)
- 制約下での優先度ベースのサーバー選択

## 関連リソース

### 必読:

- [コマンドガイド](https://github.com/khayashi4337/SuperClaude_Framework/blob/master/docs/User-Guide/commands.md)- MCPサーバーをアクティブ化するコマンド
- [クイックスタートガイド](https://github.com/khayashi4337/SuperClaude_Framework/blob/master/docs/Getting-Started/quick-start.md)- MCP セットアップガイド

### 高度な使用法:

- [行動モード](https://github.com/khayashi4337/SuperClaude_Framework/blob/master/docs/User-Guide/modes.md)- MCP調整
- [エージェントガイド](https://github.com/khayashi4337/SuperClaude_Framework/blob/master/docs/User-Guide/agents.md)- エージェントとMCPの統合
- [セッション管理](https://github.com/khayashi4337/SuperClaude_Framework/blob/master/docs/User-Guide/session-management.md)- Serena ワークフロー

### 技術リファレンス:

- [例のクックブック](https://github.com/khayashi4337/SuperClaude_Framework/blob/master/docs/Reference/examples-cookbook.md)- MCP ワークフローパターン
- [技術アーキテクチャ](https://github.com/khayashi4337/SuperClaude_Framework/blob/master/docs/Developer-Guide/technical-architecture.md)- 統合の詳細

[source: docs/User-Guide-jp/mcp-servers.md]