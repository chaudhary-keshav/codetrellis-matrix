# Gap Analysis Report: Trading UI vs Trading Platform Microservices

**Document Version:** 1.0
**Date:** January 31, 2026
**Prepared By:** System Analysis
**Status:** Analysis Complete - Pending Resolution

---

## Executive Summary

This document identifies synchronization gaps between the **Angular Trading UI** (`ai/trading-ui`) and the **Trading Platform Microservices** (`ai/trading-platform`). The analysis covers API endpoint mismatches, WebSocket event inconsistencies, data model discrepancies, and service URL configuration issues.

---

## 1. Service URL Configuration Gaps

### 1.1 Proxy Configuration Mismatch

| Location                     | Configuration                          | Expected                                              | Issue                                                             |
| ---------------------------- | -------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------- |
| `trading-ui/proxy.conf.json` | `/api` → `http://localhost:5001`       | Should be `http://localhost:3000`                     | **CRITICAL**: UI proxies to wrong port (5001 vs API Gateway 3000) |
| `trading-ui/proxy.conf.json` | `/socket.io` → `http://localhost:5001` | Should be `http://localhost:3002` (Signal Aggregator) | **CRITICAL**: WebSocket proxy to wrong service                    |

### 1.2 Direct Service URLs in Trading Service

| UI Service URL                                  | Expected Backend Service    | Port | Status     |
| ----------------------------------------------- | --------------------------- | ---- | ---------- |
| `SIGNAL_AGGREGATOR_URL = http://localhost:3002` | Signal Aggregator           | 3002 | ✅ Correct |
| `DECISION_TRACKER_URL = http://localhost:3003`  | Decision Tracker            | 3003 | ✅ Correct |
| `TRADE_EXECUTOR_URL = http://localhost:3005`    | Trade Executor              | 3005 | ✅ Correct |
| `API_URL = http://localhost:3002/api`           | Signal Aggregator API       | 3002 | ✅ Correct |
| `WS_URL = http://localhost:3002`                | Signal Aggregator WebSocket | 3002 | ✅ Correct |

### 1.3 Trading Control Service URLs

| UI Service URL                                  | Expected Backend Service | Issue      |
| ----------------------------------------------- | ------------------------ | ---------- |
| `API_GATEWAY_URL = http://localhost:3000`       | API Gateway              | ✅ Correct |
| `TRADE_EXECUTOR_URL = http://localhost:3005`    | Trade Executor           | ✅ Correct |
| `PORTFOLIO_MANAGER_URL = http://localhost:3004` | Portfolio Manager        | ✅ Correct |

---

## 2. API Endpoint Gaps

### 2.1 Trading Control Endpoints (UI → API Gateway)

| UI Calls                                 | API Gateway Endpoint                 | Backend Support | Gap                          |
| ---------------------------------------- | ------------------------------------ | --------------- | ---------------------------- |
| `POST /api/system/emergency-stop`        | `POST /system/emergency-stop`        | ✅ Implemented  | None                         |
| `POST /api/system/emergency-stop/resume` | `POST /system/emergency-stop/resume` | ✅ Implemented  | None                         |
| `GET /api/trading/mode`                  | `GET /trading/mode`                  | ✅ Implemented  | **Response format mismatch** |
| `PUT /api/trading/mode`                  | `PUT /trading/mode`                  | ✅ Implemented  | **Mode values mismatch**     |
| `PUT /api/trading/mode/:type`            | `PUT /trading/mode/:type`            | ✅ Implemented  | None                         |
| `GET /api/features`                      | `GET /features`                      | ✅ Implemented  | None                         |
| `GET /api/system/status`                 | `GET /system/status`                 | ✅ Implemented  | None                         |
| `POST /api/positions/:symbol/square-off` | `POST /positions/:symbol/square-off` | ✅ Implemented  | None                         |
| `POST /api/positions/square-off-all`     | `POST /positions/square-off-all`     | ✅ Implemented  | None                         |
| `POST /api/positions/square-off-by-type` | `POST /positions/square-off-by-type` | ✅ Implemented  | None                         |

### 2.2 Trading Mode Response Format Gap

**UI Expects (`TradingModeResponse`):**

```typescript
{
  success: boolean;
  currentMode: 'INTRADAY' | 'SWING' | 'DELIVERY';
  enabledModes: TradingModeType[];
  timestamp: string;
}
```

**Backend Returns (`/trading/mode`):**

```typescript
{
  mode: 'LIVE' | 'PAPER' | 'PAUSED';  // Different enum values!
  flags: { ... };
  timestamp: string;
}
```

**Gap:** UI uses `INTRADAY/SWING/DELIVERY` mode types, but backend uses `LIVE/PAPER/PAUSED`. These are different concepts:

- `LIVE/PAPER/PAUSED` = Trading execution mode (paper vs real money)
- `INTRADAY/SWING/DELIVERY` = Position type/strategy

### 2.3 Signal Aggregator API Endpoints

| UI Calls                      | Signal Aggregator Endpoint | Status         | Gap                                              |
| ----------------------------- | -------------------------- | -------------- | ------------------------------------------------ |
| `GET /api/status`             | `GET /api/status`          | ✅ Implemented | None                                             |
| `GET /api/signals`            | `GET /api/signals`         | ✅ Implemented | None                                             |
| `GET /api/prices`             | `GET /api/prices`          | ✅ Implemented | None                                             |
| `GET /api/positions`          | `GET /api/positions`       | ✅ Implemented | None                                             |
| `GET /api/stats`              | Not Found                  | ❌ Missing     | **UI calls `/stats` but endpoint doesn't exist** |
| `GET /api/summary`            | Not Found                  | ❌ Missing     | **Session summary endpoint missing**             |
| `GET /api/timeline`           | Not Found                  | ❌ Missing     | **Trade timeline endpoint missing**              |
| `GET /api/decisions`          | Not Found                  | ❌ Missing     | **Decision history endpoint missing**            |
| `GET /api/pnl-history`        | Not Found                  | ❌ Missing     | **PnL history endpoint missing**                 |
| `GET /api/watchlist`          | Not Found                  | ❌ Missing     | **Watchlist endpoint missing**                   |
| `GET /api/costs`              | Not Found                  | ❌ Missing     | **Trading costs endpoint missing**               |
| `POST /api/estimate-costs`    | Not Found                  | ❌ Missing     | **Cost estimation endpoint missing**             |
| `GET /api/groww/holdings`     | Not Found                  | ❌ Missing     | **Groww holdings endpoint missing**              |
| `GET /api/groww/orders`       | Not Found                  | ❌ Missing     | **Groww orders endpoint missing**                |
| `GET /api/groww/margin`       | Not Found                  | ❌ Missing     | **Groww margin endpoint missing**                |
| `GET /api/quote/:symbol`      | Not Found                  | ❌ Missing     | **Quote endpoint missing**                       |
| `POST /api/groww/place_order` | Not Found                  | ❌ Missing     | **Order placement endpoint missing**             |

### 2.4 Trade Executor API Endpoints

| UI Calls               | Trade Executor Endpoint | Status         |
| ---------------------- | ----------------------- | -------------- |
| `GET /trades`          | `GET /trades`           | ✅ Implemented |
| `POST /trades/execute` | `POST /trades/execute`  | ✅ Implemented |

### 2.5 Orchestrator API Endpoints

| UI Calls                    | Expected Endpoint                         | Status                | Gap                        |
| --------------------------- | ----------------------------------------- | --------------------- | -------------------------- |
| `POST /orchestrator/start`  | Signal Aggregator `/orchestrator/start`   | ⚠️ Needs verification | UI has fallback if missing |
| `POST /orchestrator/stop`   | Signal Aggregator `/orchestrator/stop`    | ⚠️ Needs verification | UI has fallback if missing |
| `GET /orchestrator/status`  | Signal Aggregator `/orchestrator/status`  | ⚠️ Needs verification | May not exist              |
| `GET /orchestrator/workers` | Signal Aggregator `/orchestrator/workers` | ⚠️ Needs verification | May not exist              |

### 2.6 Strategies API Endpoints

| UI Calls                    | Expected Backend                | Status                |
| --------------------------- | ------------------------------- | --------------------- |
| `GET /api/strategies/stats` | API Gateway `/strategies/stats` | ⚠️ Needs verification |

---

## 3. WebSocket Event Gaps

### 3.1 Signal Aggregator WebSocket Events

| UI Expects Event           | Backend Emits              | Status         | Gap                              |
| -------------------------- | -------------------------- | -------------- | -------------------------------- |
| `live_update`              | `live_update`              | ⚠️ Partial     | Backend may not emit this format |
| `trading_update`           | `trading_update`           | ⚠️ Partial     | Data structure may differ        |
| `session_started`          | `session_started`          | ❓ Unknown     | Needs verification               |
| `session_ended`            | `session_ended`            | ❓ Unknown     | Needs verification               |
| `trading_started`          | `trading_started`          | ❓ Unknown     | Needs verification               |
| `trading_stopped`          | `trading_stopped`          | ❓ Unknown     | Needs verification               |
| `trade_executed`           | `trade_executed`           | ✅ Implemented | Format may differ                |
| `prices`                   | `prices`                   | ✅ Implemented | Via `broadcastPrices()`          |
| `signal`                   | `signal`                   | ⚠️ Partial     | Needs `TradingSignal` format     |
| `aggregated_signal`        | `aggregated_signal`        | ❓ Unknown     | Needs verification               |
| `worker_assigned`          | `worker_assigned`          | ❓ Unknown     | Needs verification               |
| `worker_thinking`          | `worker_thinking`          | ❓ Unknown     | Needs verification               |
| `trade_marker`             | `trade_marker`             | ❓ Unknown     | Needs verification               |
| `order_status`             | `order_status`             | ❓ Unknown     | Needs verification               |
| `position_update`          | `position_update`          | ❓ Unknown     | Needs verification               |
| `scheduler_task_started`   | `scheduler_task_started`   | ❓ Unknown     | Needs verification               |
| `scheduler_task_completed` | `scheduler_task_completed` | ❓ Unknown     | Needs verification               |
| `system_health`            | `system_health`            | ❓ Unknown     | Needs verification               |
| `market_status`            | `market_status`            | ❓ Unknown     | Needs verification               |
| `pipeline_start`           | `pipeline_start`           | ❓ Unknown     | Needs verification               |
| `pipeline_progress`        | `pipeline_progress`        | ❓ Unknown     | Needs verification               |
| `pipeline_complete`        | `pipeline_complete`        | ❓ Unknown     | Needs verification               |
| `worker_bulk`              | `worker_bulk`              | ❓ Unknown     | Needs verification               |
| `signal_status`            | `signal_status`            | ❓ Unknown     | Needs verification               |
| `trade_pending`            | `trade_pending`            | ❓ Unknown     | Needs verification               |
| `trade_blocked`            | `trade_blocked`            | ❓ Unknown     | Needs verification               |
| `portfolio_update`         | `portfolio_update`         | ❓ Unknown     | Needs verification               |
| `positions_update`         | `positions_update`         | ❓ Unknown     | Needs verification               |
| `pnl_snapshot`             | `pnl_snapshot`             | ❓ Unknown     | Needs verification               |
| `scheduler_timeline`       | `scheduler_timeline`       | ❓ Unknown     | Needs verification               |

### 3.2 API Gateway WebSocket Events

| Gateway Emits        | UI Listens For     | Status                        |
| -------------------- | ------------------ | ----------------------------- |
| `signal.new`         | `signal`           | ⚠️ Name mismatch              |
| `trade.executed`     | `trade_executed`   | ⚠️ Name mismatch              |
| `decision.update`    | Not handled        | ❌ UI doesn't handle this     |
| `portfolio.update`   | `portfolio_update` | ⚠️ Name mismatch              |
| `status.update`      | Not handled        | ❌ UI doesn't handle this     |
| `worker.status`      | Not handled        | ❌ UI doesn't handle this     |
| `price.update`       | Not handled        | ❌ UI uses `prices` instead   |
| `emergencyStop`      | Not handled        | ❌ UI doesn't listen for this |
| `positionSquaredOff` | Not handled        | ❌ UI doesn't listen for this |

### 3.3 WebSocket Namespace Gap

| Component                    | Namespace     | Issue                                   |
| ---------------------------- | ------------- | --------------------------------------- |
| API Gateway `TradingGateway` | `/ws/trading` | Uses namespace                          |
| UI `trading.service.ts`      | No namespace  | **Connects to root, not `/ws/trading`** |
| UI `real-time.service.ts`    | No namespace  | **Connects to root**                    |

---

## 4. Data Model Gaps

### 4.1 Position Model Mismatch

**UI Position Interface:**

```typescript
interface Position {
  symbol: string;
  quantity: number;
  avg_price: number; // snake_case
  current_price: number; // snake_case
  pnl: number;
  pnl_pct: number; // snake_case
  positionType?: 'INTRADAY' | 'SWING' | 'DELIVERY';
}
```

**Backend Position Format (Signal Aggregator):**

```typescript
{
  symbol: string;
  quantity: number;
  avgPrice: number; // camelCase
  currentPrice: number; // camelCase
  unrealizedPnL: number; // Different name
  unrealizedPnLPercent: number; // Different name
  positionType: string;
}
```

**Gap:** Field naming conventions differ (snake_case vs camelCase) and P&L field names are different.

### 4.2 Trade Model Mismatch

**UI Trade Interface:**

```typescript
interface Trade {
  timestamp: string;
  symbol: string;
  action: string; // BUY/SELL
  quantity: number;
  price: number;
  value: number;
  pnl?: number;
  pnl_pct?: number;
  confidence: number;
  reason?: string;
  entry_price?: number;
  charges?: number;
}
```

**Backend Trade Format (Trade Executor):**

```typescript
interface Trade {
  executedAt: string; // Different field name
  symbol: string;
  type: string; // Different field name (type vs action)
  quantity: number;
  executedPrice: number; // Different field name
  requestedPrice: number;
  pnl?: number;
  pnlPercent?: number; // Different field name
  confidence?: number;
  reason?: string;
  entryPrice?: number; // camelCase
  brokerage?: number; // Different field name
  taxes?: number;
}
```

### 4.3 Signal Model Mismatch

**UI TradingSignal (simple):**

```typescript
interface TradingSignal {
  symbol: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  source: string;
  regime?: string;
  price?: number;
  timestamp?: string;
}
```

**UI TradingSignal (detailed in models):**

```typescript
interface TradingSignal {
  id: string;
  symbol: string;
  action: TradingSignalAction;
  confidence: number;
  workerId: string;
  strategyType: 'momentum' | 'breakout' | 'meanReversion' | 'scalping';
  entryPrice: number;
  stopLoss: number;
  targetPrice: number;
  riskRewardRatio: number;
  reasoningChain: ReasoningChain;
  // ... many more fields
}
```

**Gap:** Two different signal interfaces in UI with different detail levels. Backend format needs to match one or provide both.

### 4.4 Feature Flags Mismatch

**UI FeatureFlags:**

```typescript
interface FeatureFlags {
  EMERGENCY_STOP: boolean;
  PAPER_TRADING: boolean;
  SWING_TRADING: boolean;
  INTRADAY_TRADING: boolean;
  DELIVERY_TRADING: boolean;
}
```

**Backend also uses:**

- `AUTO_EXECUTION`
- `AI_ANALYSIS`
- `TRAILING_STOP`

**Gap:** Backend has additional flags not in UI interface.

### 4.5 Portfolio Model Mismatch

**UI Portfolio Interface:**

```typescript
interface Portfolio {
  total_value: number;
  cash: number;
  pnl: number;
  pnl_pct: number;
  positions_count: number;
  total_trades: number;
  gross_pnl?: number;
  total_charges?: number;
  net_pnl?: number;
}
```

**Backend PortfolioSummary (from position.model.ts):**

```typescript
interface PortfolioSummary {
  accountValue: number; // Different name
  cashAvailable: number; // Different name
  investedValue: number;
  totalExposure: number;
  exposurePercent: number;
  dailyPnL: number; // Different name
  dailyPnLPercent: number; // Different name
  totalUnrealizedPnL: number;
  totalRealizedPnL: number;
  openPositions: number; // Different name
  maxPositions: number;
  // ... more fields
}
```

---

## 5. Service Architecture Gaps

### 5.1 RealTimeService vs TradingService Duplication

Both services connect to WebSocket independently:

- `trading.service.ts` - Connects to `http://localhost:3002` directly
- `real-time.service.ts` - Connects to Signal Aggregator, Market Data, Stock Picker

**Gap:** Duplicate WebSocket connections may cause:

- Race conditions
- Inconsistent state
- Increased server load
- Memory leaks

### 5.2 Store Integration

`real-time.service.ts` updates NgRx stores:

- `MarketDataStore`
- `StockPicksStore`
- `PortfolioStore`
- `SignalsStore`
- `WorkerTileStore`
- `PipelineStore`
- `SchedulerStore`
- `SystemHealthStore`

`trading.service.ts` uses signals directly:

- `signals = signal<TradingSignal[]>([])`
- `positions = signal<Position[]>([])`
- `portfolio = signal<Portfolio | null>(null)`

**Gap:** Two separate state management approaches. Components may use either, causing inconsistent data.

---

## 6. Missing Backend Endpoints Summary

### 6.1 Signal Aggregator Missing Endpoints

| Endpoint                   | Purpose                  | Priority                 |
| -------------------------- | ------------------------ | ------------------------ |
| `GET /api/stats`           | Portfolio statistics     | HIGH                     |
| `GET /api/summary`         | Session summary          | HIGH                     |
| `GET /api/timeline`        | Trade timeline           | MEDIUM                   |
| `GET /api/decisions`       | Decision history         | MEDIUM                   |
| `GET /api/pnl-history`     | P&L history              | MEDIUM                   |
| `GET /api/watchlist`       | Watchlist                | MEDIUM                   |
| `GET /api/costs`           | Trading costs            | LOW                      |
| `POST /api/estimate-costs` | Cost estimation          | LOW                      |
| `GET /api/groww/*`         | Groww broker integration | LOW (Paper trading only) |

### 6.2 Orchestrator Missing Endpoints

| Endpoint                    | Purpose                 | Priority |
| --------------------------- | ----------------------- | -------- |
| `POST /orchestrator/start`  | Start trading           | HIGH     |
| `POST /orchestrator/stop`   | Stop trading            | HIGH     |
| `GET /orchestrator/status`  | Get orchestrator status | HIGH     |
| `GET /orchestrator/workers` | Get workers list        | HIGH     |

---

## 7. Critical Issues Ranked by Severity

### 7.1 CRITICAL (P0) - Blocks Basic Functionality

1. **Proxy Configuration Wrong Port**: `proxy.conf.json` points to port 5001 instead of 3000
2. **WebSocket Namespace Mismatch**: UI connects to root, backend uses `/ws/trading`
3. **Trading Mode Concept Mismatch**: UI uses `INTRADAY/SWING/DELIVERY`, backend uses `LIVE/PAPER/PAUSED`

### 7.2 HIGH (P1) - Major Feature Gaps

4. **Missing `/api/stats` endpoint**: Portfolio page won't load stats
5. **Missing `/api/summary` endpoint**: Session summary won't display
6. **Missing orchestrator endpoints**: Trading start/stop won't work
7. **WebSocket event name mismatches**: `signal.new` vs `signal`, etc.

### 7.3 MEDIUM (P2) - Feature Limitations

8. **Data model field naming**: snake_case vs camelCase conversions needed
9. **Duplicate WebSocket connections**: RealTimeService and TradingService both connect
10. **Missing timeline/history endpoints**: Historical data views won't work

### 7.4 LOW (P3) - Nice to Have

11. **Missing Groww integration endpoints**: Only affects live trading
12. **Missing cost estimation**: Only affects cost preview feature

---

## 8. Recommended Actions

### 8.1 Immediate Fixes (P0)

1. **Fix `proxy.conf.json`:**

   ```json
   {
     "/api": {
       "target": "http://localhost:3000",
       "secure": false,
       "changeOrigin": true
     },
     "/socket.io": {
       "target": "http://localhost:3002",
       "secure": false,
       "ws": true
     }
   }
   ```

2. **Update UI WebSocket connection to use namespace:**

   ```typescript
   // In trading.service.ts
   this.socket = io(this.WS_URL + '/ws/trading', { ... });
   ```

3. **Clarify trading mode vs position type concepts** and align UI/backend

### 8.2 Backend Endpoints to Implement

1. Signal Aggregator: `/api/stats`, `/api/summary`, `/api/timeline`
2. Orchestrator: `/start`, `/stop`, `/status`, `/workers`

### 8.3 Data Transformation Layer

Create adapters to transform between UI and backend formats:

- Position adapter
- Trade adapter
- Signal adapter
- Portfolio adapter

---

## 9. Appendix: File References

### UI Files Analyzed:

- `ai/trading-ui/proxy.conf.json`
- `ai/trading-ui/src/app/services/trading.service.ts`
- `ai/trading-ui/src/app/services/trading-control.service.ts`
- `ai/trading-ui/src/app/services/real-time.service.ts`
- `ai/trading-ui/src/app/models/position.model.ts`
- `ai/trading-ui/src/app/models/signal.model.ts`

### Backend Files Analyzed:

- `ai/trading-platform/apps/api-gateway/src/controllers/*.ts`
- `ai/trading-platform/apps/api-gateway/src/gateways/trading.gateway.ts`
- `ai/trading-platform/apps/api-gateway/src/shared/index.ts`
- `ai/trading-platform/apps/signal-aggregator/src/controllers/api.controller.ts`
- `ai/trading-platform/apps/trade-executor/src/controllers/trade.controller.ts`
- `ai/trading-platform/apps/portfolio-manager/src/controllers/portfolio.controller.ts`

---

**End of Report**
