# Stocker Data Architecture

## Data Sources

### DynamoDB (Application Data)
- User accounts and authentication
- Portfolio holdings
- Transaction history
- User preferences and settings

### External API (Stock Market Data)
- Real-time stock prices
- Historical price data
- Company information
- Market data (open, high, low, volume)

**Recommended Stock API:** IEX Cloud, Alpha Vantage, or Polygon.io

---

## DynamoDB Tables Schema

### 1. Users Table
**Purpose:** User accounts and authentication

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `email` | String | PK | User email (unique identifier) |
| `user_id` | String | GSI-PK | Unique user ID for internal references |
| `name` | String | - | Full name |
| `password_hash` | String | - | Hashed password (bcrypt) |
| `role` | String | - | `admin` or `user` |
| `status` | String | - | `active`, `inactive`, `suspended` |
| `created_at` | String (ISO 8601) | - | Account creation timestamp |
| `updated_at` | String (ISO 8601) | - | Last profile update |
| `last_login` | String (ISO 8601) | - | Last login timestamp |

**Global Secondary Index:**
- `user_id-index`: PK=`user_id`

**Example:**
```json
{
  "email": "john.smith@example.com",
  "user_id": "user#12847",
  "name": "John Smith",
  "password_hash": "$2b$12$abcdef...",
  "role": "user",
  "status": "active",
  "created_at": "2025-03-15T10:30:00Z",
  "updated_at": "2026-01-28T14:45:00Z",
  "last_login": "2026-01-28T14:45:00Z"
}
```

---

### 2. Portfolios Table
**Purpose:** User portfolio summary

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `user_id` | String | PK | User ID |
| `portfolio_id` | String | SK | Unique portfolio ID (usually "default" for main) |
| `total_value` | Number | - | Current total portfolio value in USD |
| `cash_available` | Number | - | Available cash for trading |
| `total_gain_loss` | Number | - | Total gain/loss amount |
| `total_gain_loss_percent` | Number | - | Total gain/loss percentage |
| `total_cost_basis` | Number | - | Original investment amount |
| `created_at` | String (ISO 8601) | - | Portfolio creation date |
| `updated_at` | String (ISO 8601) | - | Last portfolio update |

**Example:**
```json
{
  "user_id": "user#12847",
  "portfolio_id": "default",
  "total_value": 142847.92,
  "cash_available": 28450.00,
  "total_gain_loss": 14285.92,
  "total_gain_loss_percent": 11.11,
  "total_cost_basis": 128562.00,
  "created_at": "2025-03-15T10:30:00Z",
  "updated_at": "2026-01-28T14:45:00Z"
}
```

---

### 3. Holdings Table
**Purpose:** Current stock positions

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `user_id` | String | PK | User ID |
| `symbol` | String | SK | Stock symbol (e.g., "AAPL") |
| `shares` | Number | - | Number of shares owned |
| `avg_cost` | Number | - | Average cost per share |
| `current_price` | Number | - | Latest price (cached from API) |
| `market_value` | Number | - | Shares × current_price |
| `gain_loss` | Number | - | Market value - cost basis |
| `gain_loss_percent` | Number | - | Percentage gain/loss |
| `company_name` | String | - | Company name (cached) |
| `added_at` | String (ISO 8601) | - | When position was first opened |
| `updated_at` | String (ISO 8601) | - | Last price update |

**Global Secondary Index:**
- `symbol-index`: PK=`symbol`, SK=`user_id` (to find all users holding a stock)

**Example:**
```json
{
  "user_id": "user#12847",
  "symbol": "AAPL",
  "shares": 125,
  "avg_cost": 172.50,
  "current_price": 178.42,
  "market_value": 22302.50,
  "gain_loss": 740.00,
  "gain_loss_percent": 3.43,
  "company_name": "Apple Inc.",
  "added_at": "2025-03-15T10:30:00Z",
  "updated_at": "2026-01-28T14:45:00Z"
}
```

---

### 4. Transactions Table
**Purpose:** Trade execution history

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `user_id` | String | PK | User ID |
| `transaction_id` | String | SK | Unique transaction ID (e.g., "txn#1706458800#001") |
| `symbol` | String | - | Stock symbol |
| `action` | String | - | `BUY` or `SELL` |
| `shares` | Number | - | Number of shares in transaction |
| `price` | Number | - | Price per share at execution |
| `total` | Number | - | Shares × price |
| `status` | String | - | `COMPLETED`, `PENDING`, `FAILED`, `CANCELLED` |
| `order_type` | String | - | `MARKET`, `LIMIT`, `STOP`, `STOP_LIMIT` |
| `created_at` | String (ISO 8601) | - | Transaction timestamp |
| `settled_at` | String (ISO 8601) | - | Settlement timestamp (if applicable) |

**Global Secondary Index:**
- `symbol-created_at-index`: PK=`symbol`, SK=`created_at` (to find all trades for a stock)

**Example:**
```json
{
  "user_id": "user#12847",
  "transaction_id": "txn#1706458800#001",
  "symbol": "AAPL",
  "action": "BUY",
  "shares": 25,
  "price": 178.42,
  "total": 4460.50,
  "status": "COMPLETED",
  "order_type": "MARKET",
  "created_at": "2026-01-28T14:32:00Z",
  "settled_at": "2026-01-28T14:32:15Z"
}
```

---

### 5. StockCache Table
**Purpose:** Cached stock data to reduce external API calls

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `symbol` | String | PK | Stock symbol (e.g., "AAPL") |
| `company_name` | String | - | Company name |
| `current_price` | Number | - | Current stock price |
| `open_price` | Number | - | Today's open price |
| `high_price` | Number | - | Today's high price |
| `low_price` | Number | - | Today's low price |
| `volume` | Number | - | Trading volume |
| `market_cap` | String | - | Market capitalization |
| `pe_ratio` | Number | - | Price-to-earnings ratio |
| `updated_at` | String (ISO 8601) | - | Last update from API |
| `ttl` | Number | - | DynamoDB TTL timestamp (auto-delete old entries) |

**Example:**
```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "current_price": 178.42,
  "open_price": 175.18,
  "high_price": 179.52,
  "low_price": 174.85,
  "volume": 52400000,
  "market_cap": "2.78T",
  "pe_ratio": 29.45,
  "updated_at": "2026-01-28T14:45:00Z",
  "ttl": 1706515500
}
```

---

### 6. AdminSettings Table
**Purpose:** System-wide configuration and admin data

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `setting_key` | String | PK | Configuration key |
| `setting_value` | String | - | Configuration value |
| `updated_by` | String | - | Admin user ID who made the change |
| `updated_at` | String (ISO 8601) | - | Last update timestamp |

**Example:**
```json
{
  "setting_key": "trading_enabled",
  "setting_value": "true",
  "updated_by": "admin#1",
  "updated_at": "2026-01-28T14:45:00Z"
}
```

---

## Role-Based Access Control (RBAC)

### Admin Role
- ✅ View all users and their portfolios
- ✅ Suspend/activate user accounts
- ✅ View system-wide statistics
- ✅ View all transactions
- ✅ Access admin dashboard
- ✅ Configure system settings

### User Role
- ✅ View own portfolio
- ✅ Execute trades (buy/sell)
- ✅ View own transactions
- ✅ Update own profile
- ✅ View own settings
- ❌ Cannot view other users' data
- ❌ Cannot access admin functions

---

## Data Flow Architecture

### Stock Price Updates
```
External API (IEX/Alpha Vantage)
    ↓
Lambda/Scheduled Job (updates every 5-15 min)
    ↓
StockCache Table (DynamoDB)
    ↓
Holdings Table (updated for gains/losses)
    ↓
Portfolios Table (recalculated)
```

### User Trade Flow
```
User Submit Order (UI)
    ↓
Validate Order (Flask)
    ↓
Write Transaction (DynamoDB - PENDING)
    ↓
Process Trade (validates funds, updates Holdings)
    ↓
Update Transaction Status (COMPLETED/FAILED)
    ↓
Send SNS Notification
    ↓
Recalculate Portfolio Values
```

---

## Which Data Comes From Where

| Page | Data Source | Details |
|------|------|---------|
| **Dashboard** | DynamoDB | Portfolio summary, holdings list |
| | External API | Current stock prices for chart |
| **Buy/Sell** | External API | Stock lookup, quotes, company info |
| | DynamoDB | User's cash available, holdings |
| **Portfolio** | DynamoDB | All holdings, transaction history |
| | External API | Current prices for performance calc |
| **Transactions** | DynamoDB | Complete transaction history |
| **Settings** | DynamoDB | User preferences |
| **Admin** | DynamoDB | All users, all transactions, system metrics |

---

## Implementation Priority

1. **Phase 1 (MVP):**
   - Users table (auth)
   - Portfolios table
   - Holdings table
   - Transactions table
   - Basic role-based access

2. **Phase 2:**
   - StockCache table
   - External API integration
   - Real-time price updates

3. **Phase 3:**
   - AdminSettings table
   - Advanced admin features
   - Analytics and reporting
