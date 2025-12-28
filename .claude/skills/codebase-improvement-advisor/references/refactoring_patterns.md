# リファクタリングパターン集

## 基本的なリファクタリングパターン

### 1. Extract Method (メソッド抽出)
**目的**: 長い関数を理解しやすい小さな関数に分割する

**適用条件**:
- 関数が長すぎる（30行以上）
- 複数の処理を1つの関数で行っている
- コメントを使って処理を説明している

**実装例**:
```typescript
// Before
function generateReport(data: OrderData[]): string {
  let report = "販売レポート\n\n";
  report += "期間: " + data[0].date + " 〜 " + data[data.length-1].date + "\n\n";

  let totalSales = 0;
  let totalOrders = data.length;

  for (const order of data) {
    totalSales += order.amount;
  }

  report += "総売上: ¥" + totalSales.toLocaleString() + "\n";
  report += "総注文数: " + totalOrders + "件\n";

  const avgOrder = totalSales / totalOrders;
  report += "平均注文額: ¥" + avgOrder.toLocaleString() + "\n\n";

  report += "日別売上\n";
  report += "--------\n";

  const dailySales: { [key: string]: number } = {};
  for (const order of data) {
    const date = order.date;
    if (!dailySales[date]) {
      dailySales[date] = 0;
    }
    dailySales[date] += order.amount;
  }

  for (const date in dailySales) {
    report += date + ": ¥" + dailySales[date].toLocaleString() + "\n";
  }

  return report;
}

// After
function generateReport(data: OrderData[]): string {
  let report = createHeader(data);
  report += calculateSummaryStats(data);
  report += generateDailySales(data);
  return report;
}

function createHeader(data: OrderData[]): string {
  return `販売レポート\n\n期間: ${data[0].date} 〜 ${data[data.length-1].date}\n\n`;
}

function calculateSummaryStats(data: OrderData[]): string {
  const totalSales = data.reduce((sum, order) => sum + order.amount, 0);
  const totalOrders = data.length;
  const avgOrder = totalSales / totalOrders;

  return `総売上: ¥${totalSales.toLocaleString()}\n` +
         `総注文数: ${totalOrders}件\n` +
         `平均注文額: ¥${avgOrder.toLocaleString()}\n\n`;
}

function generateDailySales(data: OrderData[]): string {
  const dailySales = aggregateDailySales(data);
  let report = "日別売上\n--------\n";

  for (const [date, amount] of Object.entries(dailySales)) {
    report += `${date}: ¥${amount.toLocaleString()}\n`;
  }

  return report;
}

function aggregateDailySales(data: OrderData[]): { [key: string]: number } {
  const dailySales: { [key: string]: number } = {};
  for (const order of data) {
    dailySales[order.date] = (dailySales[order.date] || 0) + order.amount;
  }
  return dailySales;
}
```

### 2. Extract Variable (変数抽出)
**目的**: 複雑な式や意味のある値に名前を付ける

**適用条件**:
- 複雑な計算式がある
- マジックナンバーがある
- 条件式が読みにくい

**実装例**:
```typescript
// Before
function calculateDiscount(price: number, customerLevel: string, isPremiumMember: boolean): number {
  if (price > 10000 && (customerLevel === 'gold' || customerLevel === 'platinum') && isPremiumMember) {
    return price * 0.85;
  } else if (price > 5000 && (customerLevel === 'gold' || customerLevel === 'platinum')) {
    return price * 0.9;
  } else if (price > 3000 && customerLevel === 'silver') {
    return price * 0.95;
  }
  return price;
}

// After
function calculateDiscount(price: number, customerLevel: string, isPremiumMember: boolean): number {
  const HIGH_VALUE_THRESHOLD = 10000;
  const MEDIUM_VALUE_THRESHOLD = 5000;
  const LOW_VALUE_THRESHOLD = 3000;
  const PREMIUM_DISCOUNT_RATE = 0.85;
  const GOLD_DISCOUNT_RATE = 0.9;
  const SILVER_DISCOUNT_RATE = 0.95;

  const isHighValueOrder = price > HIGH_VALUE_THRESHOLD;
  const isMediumValueOrder = price > MEDIUM_VALUE_THRESHOLD;
  const isLowValueOrder = price > LOW_VALUE_THRESHOLD;
  const isPremiumCustomer = ['gold', 'platinum'].includes(customerLevel);
  const isSilverCustomer = customerLevel === 'silver';

  if (isHighValueOrder && isPremiumCustomer && isPremiumMember) {
    return price * PREMIUM_DISCOUNT_RATE;
  } else if (isMediumValueOrder && isPremiumCustomer) {
    return price * GOLD_DISCOUNT_RATE;
  } else if (isLowValueOrder && isSilverCustomer) {
    return price * SILVER_DISCOUNT_RATE;
  }

  return price;
}
```

### 3. Replace Magic Number with Symbolic Constant (マジックナンバーの置き換え)
**目的**: 数値リテラルに意味のある名前を付ける

**実装例**:
```typescript
// Before
class DeliveryCalculator {
  calculateDistance(zip1: string, zip2: string): number {
    // 緯度経度の差から距離を計算
    const latDiff = Math.abs(parseInt(zip1.slice(0, 3)) - parseInt(zip2.slice(0, 3)));
    const lonDiff = Math.abs(parseInt(zip1.slice(3, 6)) - parseInt(zip2.slice(3, 6)));
    return Math.sqrt(latDiff * latDiff + lonDiff * lonDiff) * 111;
  }

  calculateFee(distance: number): number {
    if (distance < 5) return 500;
    if (distance < 20) return 800;
    if (distance < 50) return 1200;
    return 1500;
  }
}

// After
class DeliveryCalculator {
  private static readonly EARTH_RADIUS_KM = 111;
  private static readonly SHORT_DISTANCE_THRESHOLD = 5;
  private static readonly MEDIUM_DISTANCE_THRESHOLD = 20;
  private static readonly LONG_DISTANCE_THRESHOLD = 50;

  private static readonly SHORT_DISTANCE_FEE = 500;
  private static readonly MEDIUM_DISTANCE_FEE = 800;
  private static readonly LONG_DISTANCE_FEE = 1200;
  private static readonly EXTRA_LONG_DISTANCE_FEE = 1500;

  calculateDistance(zip1: string, zip2: string): number {
    const latDiff = this.getCoordinateDiff(zip1, zip2, 'lat');
    const lonDiff = this.getCoordinateDiff(zip1, zip2, 'lon');
    const distance = Math.sqrt(latDiff * latDiff + lonDiff * lonDiff);
    return distance * DeliveryCalculator.EARTH_RADIUS_KM;
  }

  calculateFee(distance: number): number {
    if (distance < DeliveryCalculator.SHORT_DISTANCE_THRESHOLD) {
      return DeliveryCalculator.SHORT_DISTANCE_FEE;
    }
    if (distance < DeliveryCalculator.MEDIUM_DISTANCE_THRESHOLD) {
      return DeliveryCalculator.MEDIUM_DISTANCE_FEE;
    }
    if (distance < DeliveryCalculator.LONG_DISTANCE_THRESHOLD) {
      return DeliveryCalculator.LONG_DISTANCE_FEE;
    }
    return DeliveryCalculator.EXTRA_LONG_DISTANCE_FEE;
  }

  private getCoordinateDiff(zip1: string, zip2: string, type: 'lat' | 'lon'): number {
    const start = type === 'lat' ? 0 : 3;
    const end = start + 3;
    return Math.abs(parseInt(zip1.slice(start, end)) - parseInt(zip2.slice(start, end)));
  }
}
```

### 4. Replace Conditional with Polymorphism (条件分岐のポリモーフィズム化)
**目的**: 複雑な条件分岐をオブジェクト指向の設計に置き換える

**実装例**:
```typescript
// Before
class PaymentProcessor {
  processPayment(amount: number, paymentMethod: string): void {
    if (paymentMethod === 'credit_card') {
      this.processCreditCard(amount);
    } else if (paymentMethod === 'bank_transfer') {
      this.processBankTransfer(amount);
    } else if (paymentMethod === 'digital_wallet') {
      this.processDigitalWallet(amount);
    } else if (paymentMethod === 'cryptocurrency') {
      this.processCryptocurrency(amount);
    }
  }

  calculateFee(amount: number, paymentMethod: string): number {
    if (paymentMethod === 'credit_card') {
      return amount * 0.03; // 3%
    } else if (paymentMethod === 'bank_transfer') {
      return Math.max(200, amount * 0.001); // 0.1% or 200円
    } else if (paymentMethod === 'digital_wallet') {
      return Math.max(100, amount * 0.005); // 0.5% or 100円
    } else if (paymentMethod === 'cryptocurrency') {
      return Math.max(500, amount * 0.01); // 1% or 500円
    }
    return 0;
  }

  private processCreditCard(amount: number): void {
    // クレジットカード処理ロジック
  }

  private processBankTransfer(amount: number): void {
    // 銀行振込処理ロジック
  }

  private processDigitalWallet(amount: number): void {
    // デジタルウォレット処理ロジック
  }

  private processCryptocurrency(amount: number): void {
    // 暗号通貨処理ロジック
  }
}

// After
abstract class PaymentMethod {
  abstract processPayment(amount: number): void;
  abstract calculateFee(amount: number): number;
  abstract getMethodName(): string;
}

class CreditCardPayment extends PaymentMethod {
  private static readonly FEE_RATE = 0.03;

  processPayment(amount: number): void {
    console.log(`クレジットカードで¥${amount}を処理します`);
    // クレジットカード固有の処理
  }

  calculateFee(amount: number): number {
    return amount * CreditCardPayment.FEE_RATE;
  }

  getMethodName(): string {
    return 'credit_card';
  }
}

class BankTransferPayment extends PaymentMethod {
  private static readonly FEE_RATE = 0.001;
  private static readonly MINIMUM_FEE = 200;

  processPayment(amount: number): void {
    console.log(`銀行振込で¥${amount}を処理します`);
    // 銀行振込固有の処理
  }

  calculateFee(amount: number): number {
    return Math.max(BankTransferPayment.MINIMUM_FEE, amount * BankTransferPayment.FEE_RATE);
  }

  getMethodName(): string {
    return 'bank_transfer';
  }
}

class DigitalWalletPayment extends PaymentMethod {
  private static readonly FEE_RATE = 0.005;
  private static readonly MINIMUM_FEE = 100;

  processPayment(amount: number): void {
    console.log(`デジタルウォレットで¥${amount}を処理します`);
    // デジタルウォレット固有の処理
  }

  calculateFee(amount: number): number {
    return Math.max(DigitalWalletPayment.MINIMUM_FEE, amount * DigitalWalletPayment.FEE_RATE);
  }

  getMethodName(): string {
    return 'digital_wallet';
  }
}

class CryptocurrencyPayment extends PaymentMethod {
  private static readonly FEE_RATE = 0.01;
  private static readonly MINIMUM_FEE = 500;

  processPayment(amount: number): void {
    console.log(`暗号通貨で¥${amount}を処理します`);
    // 暗号通貨固有の処理
  }

  calculateFee(amount: number): number {
    return Math.max(CryptocurrencyPayment.MINIMUM_FEE, amount * CryptocurrencyPayment.FEE_RATE);
  }

  getMethodName(): string {
    return 'cryptocurrency';
  }
}

class PaymentMethodFactory {
  private static methods = new Map<string, PaymentMethod>([
    ['credit_card', new CreditCardPayment()],
    ['bank_transfer', new BankTransferPayment()],
    ['digital_wallet', new DigitalWalletPayment()],
    ['cryptocurrency', new CryptocurrencyPayment()]
  ]);

  static create(methodName: string): PaymentMethod {
    const method = this.methods.get(methodName);
    if (!method) {
      throw new Error(`不明な支払い方法: ${methodName}`);
    }
    return method;
  }
}

class PaymentProcessor {
  processPayment(amount: number, paymentMethod: string): void {
    const method = PaymentMethodFactory.create(paymentMethod);
    method.processPayment(amount);
  }

  calculateFee(amount: number, paymentMethod: string): number {
    const method = PaymentMethodFactory.create(paymentMethod);
    return method.calculateFee(amount);
  }
}
```

### 5. Extract Class (クラス抽出)
**目的**: 1つのクラスが複数の責務を持っている場合に分割する

**実装例**:
```typescript
// Before
class Employee {
  constructor(
    public id: string,
    public name: string,
    public email: string,
    public department: string,
    public position: string,
    public salary: number,
    public hireDate: Date,
    public address: string,
    public phone: string,
    public emergencyContact: string,
    public emergencyPhone: string
  ) {}

  calculateBonus(): number {
    const yearsOfService = this.getYearsOfService();
    const baseBonus = this.salary * 0.1;
    return baseBonus * (1 + yearsOfService * 0.02);
  }

  getYearsOfService(): number {
    const now = new Date();
    return Math.floor((now.getTime() - this.hireDate.getTime()) / (365 * 24 * 60 * 60 * 1000));
  }

  promote(newPosition: string, salaryIncrease: number): void {
    this.position = newPosition;
    this.salary += salaryIncrease;
  }

  updateAddress(newAddress: string, newPhone: string): void {
    this.address = newAddress;
    this.phone = newPhone;
  }

  updateEmergencyContact(contact: string, phone: string): void {
    this.emergencyContact = contact;
    this.emergencyPhone = phone;
  }

  sendEmail(message: string): void {
    console.log(`Sending email to ${this.email}: ${message}`);
  }
}

// After
class PersonalInfo {
  constructor(
    public name: string,
    public email: string,
    public address: string,
    public phone: string
  ) {}

  sendEmail(message: string): void {
    console.log(`Sending email to ${this.email}: ${message}`);
  }

  updateContactInfo(address: string, phone: string): void {
    this.address = address;
    this.phone = phone;
  }
}

class EmergencyContact {
  constructor(
    public contactName: string,
    public phoneNumber: string
  ) {}

  updateContact(contactName: string, phoneNumber: string): void {
    this.contactName = contactName;
    this.phoneNumber = phoneNumber;
  }
}

class EmploymentInfo {
  constructor(
    public department: string,
    public position: string,
    public salary: number,
    public hireDate: Date
  ) {}

  calculateBonus(): number {
    const yearsOfService = this.getYearsOfService();
    const baseBonus = this.salary * 0.1;
    return baseBonus * (1 + yearsOfService * 0.02);
  }

  getYearsOfService(): number {
    const now = new Date();
    return Math.floor((now.getTime() - this.hireDate.getTime()) / (365 * 24 * 60 * 60 * 1000));
  }

  promote(newPosition: string, salaryIncrease: number): void {
    this.position = newPosition;
    this.salary += salaryIncrease;
  }
}

class Employee {
  private personalInfo: PersonalInfo;
  private emergencyContact: EmergencyContact;
  private employmentInfo: EmploymentInfo;

  constructor(
    public id: string,
    name: string,
    email: string,
    department: string,
    position: string,
    salary: number,
    hireDate: Date,
    address: string,
    phone: string,
    emergencyContactName: string,
    emergencyPhone: string
  ) {
    this.personalInfo = new PersonalInfo(name, email, address, phone);
    this.emergencyContact = new EmergencyContact(emergencyContactName, emergencyPhone);
    this.employmentInfo = new EmploymentInfo(department, position, salary, hireDate);
  }

  // Getters
  get name(): string { return this.personalInfo.name; }
  get email(): string { return this.personalInfo.email; }
  get department(): string { return this.employmentInfo.department; }
  get position(): string { return this.employmentInfo.position; }
  get salary(): number { return this.employmentInfo.salary; }

  // Delegated methods
  calculateBonus(): number {
    return this.employmentInfo.calculateBonus();
  }

  getYearsOfService(): number {
    return this.employmentInfo.getYearsOfService();
  }

  promote(newPosition: string, salaryIncrease: number): void {
    this.employmentInfo.promote(newPosition, salaryIncrease);
  }

  updateAddress(newAddress: string, newPhone: string): void {
    this.personalInfo.updateContactInfo(newAddress, newPhone);
  }

  updateEmergencyContact(contactName: string, phoneNumber: string): void {
    this.emergencyContact.updateContact(contactName, phoneNumber);
  }

  sendEmail(message: string): void {
    this.personalInfo.sendEmail(message);
  }
}
```

### 6. Introduce Parameter Object (パラメータオブジェクトの導入)
**目的**: 多くのパラメータを持つメソッドを整理する

**実装例**:
```typescript
// Before
function createUser(
  name: string,
  email: string,
  password: string,
  firstName: string,
  lastName: string,
  phone: string,
  address: string,
  city: string,
  state: string,
  zipCode: string,
  country: string,
  dateOfBirth: Date,
  gender: string,
  newsletterOptIn: boolean
): User {
  // ユーザー作成ロジック
}

function updateUser(
  id: string,
  name?: string,
  email?: string,
  firstName?: string,
  lastName?: string,
  phone?: string,
  address?: string,
  city?: string,
  state?: string,
  zipCode?: string,
  country?: string,
  dateOfBirth?: Date,
  gender?: string,
  newsletterOptIn?: boolean
): User {
  // ユーザー更新ロジック
}

// After
class PersonalDetails {
  constructor(
    public firstName: string,
    public lastName: string,
    public phone: string,
    public dateOfBirth: Date,
    public gender: string
  ) {}
}

class Address {
  constructor(
    public street: string,
    public city: string,
    public state: string,
    public zipCode: string,
    public country: string
  ) {}
}

class UserPreferences {
  constructor(
    public newsletterOptIn: boolean = false
  ) {}
}

class UserData {
  constructor(
    public name: string,
    public email: string,
    public password: string,
    public personalDetails: PersonalDetails,
    public address: Address,
    public preferences: UserPreferences = new UserPreferences()
  ) {}

  // バリデーション
  validate(): string[] {
    const errors: string[] = [];

    if (!this.name || this.name.length < 2) {
      errors.push('名前は2文字以上で入力してください');
    }

    if (!this.email || !this.isValidEmail(this.email)) {
      errors.push('有効なメールアドレスを入力してください');
    }

    if (!this.password || this.password.length < 8) {
      errors.push('パスワードは8文字以上で入力してください');
    }

    return errors;
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}

function createUserData(
  name: string,
  email: string,
  password: string,
  personalDetails: PersonalDetails,
  address: Address,
  preferences?: UserPreferences
): User {
  const userData = new UserData(name, email, password, personalDetails, address, preferences);

  const errors = userData.validate();
  if (errors.length > 0) {
    throw new Error(`バリデーションエラー: ${errors.join(', ')}`);
  }

  // ユーザー作成ロジック
  return new User(userData);
}

function updateUser(id: string, updates: Partial<UserData>): User {
  // 既存ユーザーを取得
  const existingUser = getUserById(id);

  // 更新データを適用
  if (updates.name) existingUser.userData.name = updates.name;
  if (updates.email) existingUser.userData.email = updates.email;
  if (updates.personalDetails) existingUser.userData.personalDetails = updates.personalDetails;
  if (updates.address) existingUser.userData.address = updates.address;
  if (updates.preferences) existingUser.userData.preferences = updates.preferences;

  return existingUser;
}
```

### 7. Replace Nested Conditional with Guard Clauses (ガード節によるネストの置き換え)
**目的**: 深いネストをなくしてコードを読みやすくする

**実装例**:
```typescript
// Before
function calculateInsurancePremium(age: number, hasAccidents: boolean, isSmoker: boolean, hasPreExistingConditions: boolean): number {
  let basePremium = 100;

  if (age >= 18) {
    if (age <= 65) {
      if (!hasAccidents) {
        if (!isSmoker) {
          if (!hasPreExistingConditions) {
            basePremium *= 1.0;
          } else {
            basePremium *= 1.5;
          }
        } else {
          if (!hasPreExistingConditions) {
            basePremium *= 1.3;
          } else {
            basePremium *= 2.0;
          }
        }
      } else {
        if (!isSmoker) {
          if (!hasPreExistingConditions) {
            basePremium *= 1.2;
          } else {
            basePremium *= 1.8;
          }
        } else {
          if (!hasPreExistingConditions) {
            basePremium *= 1.6;
          } else {
            basePremium *= 2.5;
          }
        }
      }
    } else {
      if (!hasAccidents) {
        if (!isSmoker) {
          if (!hasPreExistingConditions) {
            basePremium *= 2.0;
          } else {
            basePremium *= 3.0;
          }
        } else {
          if (!hasPreExistingConditions) {
            basePremium *= 2.5;
          } else {
            basePremium *= 4.0;
          }
        }
      } else {
        if (!isSmoker) {
          if (!hasPreExistingConditions) {
            basePremium *= 2.5;
          } else {
            basePremium *= 3.5;
          }
        } else {
          if (!hasPreExistingConditions) {
            basePremium *= 3.0;
          } else {
            basePremium *= 5.0;
          }
        }
      }
    }
  } else {
    basePremium = 0;
  }

  return basePremium;
}

// After
function calculateInsurancePremium(age: number, hasAccidents: boolean, isSmoker: boolean, hasPreExistingConditions: boolean): number {
  const BASE_PREMIUM = 100;

  // ガード節：年齢チェック
  if (age < 18 || age > 65) {
    return 0;
  }

  let multiplier = 1.0;

  // リスクファクターの加算
  if (hasAccidents) multiplier += 0.5;
  if (isSmoker) multiplier += 0.6;
  if (hasPreExistingConditions) multiplier += 1.0;

  // 年齢による調整
  if (age > 50) multiplier += 1.5;

  return BASE_PREMIUM * multiplier;
}

// さらに改善したバージョン
class InsuranceCalculator {
  private static readonly BASE_PREMIUM = 100;
  private static readonly AGE_LIMITS = { MIN: 18, MAX: 65 };
  private static readonly SENIOR_AGE = 50;

  private static readonly RISK_FACTORS = {
    ACCIDENTS: 0.5,
    SMOKING: 0.6,
    PRE_EXISTING_CONDITIONS: 1.0,
    SENIOR_AGE: 1.5
  };

  static calculatePremium(
    age: number,
    hasAccidents: boolean,
    isSmoker: boolean,
    hasPreExistingConditions: boolean
  ): number {
    // ガード節：対象年齢チェック
    if (!this.isEligibleAge(age)) {
      return 0;
    }

    const riskMultiplier = this.calculateRiskMultiplier(
      age, hasAccidents, isSmoker, hasPreExistingConditions
    );

    return this.BASE_PREMIUM * riskMultiplier;
  }

  private static isEligibleAge(age: number): boolean {
    return age >= this.AGE_LIMITS.MIN && age <= this.AGE_LIMITS.MAX;
  }

  private static calculateRiskMultiplier(
    age: number,
    hasAccidents: boolean,
    isSmoker: boolean,
    hasPreExistingConditions: boolean
  ): number {
    let multiplier = 1.0;

    if (hasAccidents) multiplier += this.RISK_FACTORS.ACCIDENTS;
    if (isSmoker) multiplier += this.RISK_FACTORS.SMOKING;
    if (hasPreExistingConditions) multiplier += this.RISK_FACTORS.PRE_EXISTING_CONDITIONS;
    if (age > this.SENIOR_AGE) multiplier += this.RISK_FACTORS.SENIOR_AGE;

    return multiplier;
  }
}
```

## まとめ

これらのリファクタリングパターンを適用することで：

1. **可読性の向上**: コードが理解しやすくなる
2. **保守性の向上**: 変更容易性が高くなる
3. **再利用性の向上**: コード部品が再利用しやすくなる
4. **バグの減少**: 複雑性が減り、バグが入りにくくなる
5. **テスト容易性**: 小さな関数/クラスがテストしやすくなる

リファクタリングは継続的なプロセスです。定期的にコードを見直し、改善の機会を探すことが重要です。