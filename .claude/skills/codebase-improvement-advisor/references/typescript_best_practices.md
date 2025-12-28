# TypeScript ベストプラクティス

## コード品質基準

### 1. 型安全性

#### 厳格な型定義
```typescript
// ✅ 良い例
interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

function getUser(id: string): Promise<User | null> {
  // 実装
}

// ❌ 悪い例
function getUser(id: any): any {
  // 実装
}
```

#### Union Types の活用
```typescript
// ✅ 良い例
type Status = 'pending' | 'approved' | 'rejected';

interface ApiResponse<T> {
  data: T;
  status: Status;
  message?: string;
}

// ❌ 悪い例
interface ApiResponse {
  data: any;
  status: string;
  message?: string;
}
```

### 2. 関数設計

#### 関数の単一責任
```typescript
// ✅ 良い例: 1つの関数で1つのことだけ
function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

function saveUser(user: User): Promise<void> {
  return database.save(user);
}

// ❌ 悪い例: 複数の責務
function validateAndSaveUser(email: string, name: string): Promise<void> {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email');
  }

  const user = { email, name };
  return database.save(user);
}
```

#### 純粋関数の優先
```typescript
// ✅ 良い例: 副作用のない純粋関数
function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// ❌ 悪い例: 副作用のある関数
let total = 0;
function addToTotal(price: number): void {
  total += price;
}
```

### 3. エラーハンドリング

#### Result パターン
```typescript
// ✅ 良い例: Result 型でのエラーハンドリング
type Result<T, E = Error> = {
  success: true;
  data: T;
} | {
  success: false;
  error: E;
};

function safeDivide(a: number, b: number): Result<number> {
  if (b === 0) {
    return {
      success: false,
      error: new Error('Division by zero')
    };
  }

  return {
    success: true,
    data: a / b
  };
}
```

#### カスタムエラー型
```typescript
// ✅ 良い例: 特定のエラー型
class ValidationError extends Error {
  constructor(
    message: string,
    public readonly field: string
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

class NetworkError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number
  ) {
    super(message);
    this.name = 'NetworkError';
  }
}
```

### 4. 非同期処理

#### Promise の適切な使用
```typescript
// ✅ 良い例: async/await
async function fetchUserData(userId: string): Promise<User> {
  try {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) {
      throw new NetworkError('Failed to fetch user', response.status);
    }
    return response.json();
  } catch (error) {
    if (error instanceof NetworkError) {
      throw error;
    }
    throw new Error('Unexpected error occurred');
  }
}

// ❌ 悪い例: ネストされたコールバック
function fetchUserData(userId: string, callback: (user: User) => void): void {
  fetch(`/api/users/${userId}`, (response) => {
    if (!response.ok) {
      callback(null);
      return;
    }
    response.json((user) => {
      callback(user);
    });
  });
}
```

### 5. パフォーマンス

#### メモ化の活用
```typescript
// ✅ 良い例: useMemo での計算結果のキャッシュ
import { useMemo } from 'react';

function ExpensiveComponent({ items }: { items: Item[] }) {
  const expensiveValue = useMemo(() => {
    return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }, [items]);

  return <div>Total: {expensiveValue}</div>;
}
```

#### 遅延初期化
```typescript
// ✅ 良い例: 遅延初期化
class DatabaseConnection {
  private _connection: Connection | null = null;

  get connection(): Connection {
    if (!this._connection) {
      this._connection = createConnection();
    }
    return this._connection;
  }
}
```

### 6. コード組織

#### モジュール分割
```typescript
// ✅ 良い例: 機能ごとのモジュール分割
// user/types.ts
export interface User {
  id: string;
  name: string;
  email: string;
}

// user/validation.ts
import { User } from './types';

export function validateUser(user: Partial<User>): ValidationResult {
  // バリデーションロジック
}

// user/service.ts
import { User } from './types';
import { validateUser } from './validation';

export class UserService {
  async createUser(userData: Partial<User>): Promise<User> {
    // ユーザー作成ロジック
  }
}
```

## リファクタリングパターン

### 1. Extract Method (メソッド抽出)
**問題**: 長い関数が複数の処理をしている
```typescript
// ❌ 改善前
function processOrder(order: Order): void {
  // 注文の検証
  if (!order.items || order.items.length === 0) {
    throw new Error('Order must have items');
  }

  // 在庫確認
  for (const item of order.items) {
    const stock = checkStock(item.productId);
    if (stock < item.quantity) {
      throw new Error(`Insufficient stock for ${item.productId}`);
    }
  }

  // 価格計算
  let total = 0;
  for (const item of order.items) {
    total += item.price * item.quantity;
  }

  // 注文保存
  const savedOrder = saveOrder(order);
}

// ✅ 改善後
function processOrder(order: Order): void {
  validateOrder(order);
  checkInventory(order);
  const total = calculateTotal(order);
  saveOrder(order);
}

function validateOrder(order: Order): void {
  if (!order.items || order.items.length === 0) {
    throw new Error('Order must have items');
  }
}

function checkInventory(order: Order): void {
  for (const item of order.items) {
    const stock = checkStock(item.productId);
    if (stock < item.quantity) {
      throw new Error(`Insufficient stock for ${item.productId}`);
    }
  }
}

function calculateTotal(order: Order): number {
  return order.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}
```

### 2. Extract Constant (定数抽出)
**問題**: マジックナンバーや文字列リテラルが散在している
```typescript
// ❌ 改善前
function calculateShippingCost(weight: number, distance: number): number {
  return Math.max(500, weight * 100 + distance * 50);
}

function applyDiscount(price: number, customerLevel: string): number {
  if (customerLevel === 'premium') {
    return price * 0.9;
  } else if (customerLevel === 'gold') {
    return price * 0.8;
  }
  return price;
}

// ✅ 改善後
const MINIMUM_SHIPPING_COST = 500;
const WEIGHT_MULTIPLIER = 100;
const DISTANCE_MULTIPLIER = 50;

const DISCOUNT_RATES = {
  premium: 0.9,
  gold: 0.8,
} as const;

type CustomerLevel = keyof typeof DISCOUNT_RATES;

function calculateShippingCost(weight: number, distance: number): number {
  return Math.max(
    MINIMUM_SHIPPING_COST,
    weight * WEIGHT_MULTIPLIER + distance * DISTANCE_MULTIPLIER
  );
}

function applyDiscount(price: number, customerLevel: CustomerLevel): number {
  const discount = DISCOUNT_RATES[customerLevel];
  return discount ? price * discount : price;
}
```

### 3. Replace Conditional with Polymorphism (条件分岐のポリモーフィズム化)
**問題**: 複雑な条件分岐が多い
```typescript
// ❌ 改善前
function calculatePrice(item: Item): number {
  if (item.type === 'book') {
    return item.basePrice * 0.9; // 本は10%割引
  } else if (item.type === 'electronics') {
    return item.basePrice * 1.1; // 電子製品は10%増税
  } else if (item.type === 'clothing') {
    return item.basePrice * 0.95; // 衣類は5%割引
  }
  return item.basePrice;
}

// ✅ 改善後
abstract class PricingStrategy {
  abstract calculate(basePrice: number): number;
}

class BookPricing extends PricingStrategy {
  calculate(basePrice: number): number {
    return basePrice * 0.9;
  }
}

class ElectronicsPricing extends PricingStrategy {
  calculate(basePrice: number): number {
    return basePrice * 1.1;
  }
}

class ClothingPricing extends PricingStrategy {
  calculate(basePrice: number): number {
    return basePrice * 0.95;
  }
}

class DefaultPricing extends PricingStrategy {
  calculate(basePrice: number): number {
    return basePrice;
  }
}

function calculatePrice(item: Item): number {
  const strategy = this.getPricingStrategy(item.type);
  return strategy.calculate(item.basePrice);
}
```

## セキュリティベストプラクティス

### 1. 入力検証
```typescript
// ✅ 良い例: 厳格な入力検証
function sanitizeInput(input: string): string {
  return input
    .trim()
    .replace(/[<>]/g, '') // HTMLタグを除去
    .substring(0, 1000);  // 長さを制限
}

function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email) && email.length <= 254;
}
```

### 2. SQLインジェクション防止
```typescript
// ✅ 良い例: パラメータ化クエリ
async function getUserById(id: string): Promise<User> {
  const query = 'SELECT * FROM users WHERE id = $1';
  const result = await db.query(query, [id]);
  return result.rows[0];
}

// ❌ 悪い例: 文字列連結
async function getUserById(id: string): Promise<User> {
  const query = `SELECT * FROM users WHERE id = '${id}'`;
  const result = await db.query(query);
  return result.rows[0];
}
```

### 3. 認証と認可
```typescript
// ✅ 良い例: JWTトークン検証
import jwt from 'jsonwebtoken';

interface AuthPayload {
  userId: string;
  role: string;
}

function verifyToken(token: string): AuthPayload | null {
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as AuthPayload;
    return payload;
  } catch (error) {
    return null;
  }
}

function requireAuth(req: Request, res: Response, next: NextFunction): void {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    res.status(401).json({ error: 'No token provided' });
    return;
  }

  const payload = verifyToken(token);
  if (!payload) {
    res.status(401).json({ error: 'Invalid token' });
    return;
  }

  req.user = payload;
  next();
}
```

## テスト戦略

### 1. ユニットテスト
```typescript
// ✅ 良い例: 純粋関数のテスト
describe('calculateTotal', () => {
  it('should calculate total correctly for empty array', () => {
    expect(calculateTotal([])).toBe(0);
  });

  it('should calculate total correctly for multiple items', () => {
    const items = [
      { price: 100, quantity: 2 },
      { price: 50, quantity: 3 }
    ];
    expect(calculateTotal(items)).toBe(350);
  });
});
```

### 2. モックの使用
```typescript
// ✅ 良い例: 適切なモック
describe('UserService', () => {
  let userService: UserService;
  let mockDatabase: jest.Mocked<Database>;

  beforeEach(() => {
    mockDatabase = {
      save: jest.fn(),
      findById: jest.fn()
    } as any;

    userService = new UserService(mockDatabase);
  });

  it('should save user successfully', async () => {
    const user = { id: '1', name: 'John', email: 'john@example.com' };
    mockDatabase.save.mockResolvedValue(user);

    const result = await userService.createUser(user);

    expect(mockDatabase.save).toHaveBeenCalledWith(user);
    expect(result).toEqual(user);
  });
});
```

## パフォーマンス最適化

### 1. メモリ使用量の最適化
```typescript
// ✅ 良い例: WeakMap の使用
class UserCache {
  private cache = new WeakMap<object, UserData>();

  get(user: object): UserData | undefined {
    return this.cache.get(user);
  }

  set(user: object, data: UserData): void {
    this.cache.set(user, data);
  }
}
```

### 2. 非同期処理の最適化
```typescript
// ✅ 良い例: Promise.all での並列処理
async function fetchMultipleUsers(userIds: string[]): Promise<User[]> {
  const promises = userIds.map(id => fetchUser(id));
  return Promise.all(promises);
}

// ❌ 悪い例: 順次処理
async function fetchMultipleUsers(userIds: string[]): Promise<User[]> {
  const users: User[] = [];
  for (const id of userIds) {
    const user = await fetchUser(id);
    users.push(user);
  }
  return users;
}
```

これらのベストプラクティスを遵守することで、保守性が高く、バグの少ないコードベースを維持できます。