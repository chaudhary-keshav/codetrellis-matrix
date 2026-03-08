# UI-Backend Sync Gap Analysis Report

**Project:** trading-ui ↔ trading-platform
**Date:** 2026-01-31
**Status:** 🔴 Critical Sync Issues Found
**Analyst:** AI Code Review

---

## Executive Summary

The Angular UI (`trading-ui`) and NestJS microservices (`trading-platform`) have **significant contract mismatches** that prevent proper real-time data synchronization. This report identifies all gaps between the UI's expected API contracts and the backend's actual implementations.

---

## 1. WebSocket Namespace Mismatches 🚨 CRITICAL

### Issue: UI connects to root namespace, backends use custom namespaces

| Service           | Port | UI Expects | Backend Provides | Status      |
| ----------------- | ---- | ---------- | ---------------- | ----------- |
| Signal Aggregator | 3002 | `/` (root) | `/` (root)       | ✅ OK       |
| Market Data       | 3001 | `/` (root) | `/market-data`   | 🔴 MISMATCH |
| API Gateway       | 3000 | N/A        | `/ws/trading`    | ⚠️ Unused   |

### Affected Files

**UI Side:**

- `ai/trading-ui/src/app/services/real-time.service.ts` (lines 63-65)

```typescript
private readonly DEFAULT_SIGNAL_AGGREGATOR_URL = 'http://localhost:3002';
private readonly DEFAULT_MARKET_DATA_URL = 'http://localhost:3001';
private readonly DEFAULT_STOCK_PICKER_URL = 'http://localhost:3001';
```

**Backend Side:**

- `ai/trading-platform/apps/market-data/src/gateways/market-data.gateway.ts` (line 18)

```typescript
namespace: '/market-data',  // ❌ UI expects root namespace
```

### Fix Required

Change market-data gateway to use root namespace:

```typescript
@WebSocketGateway({
  cors: { origin: ['http://localhost:4200', 'http://localhost:3000', '*'], credentials: true },
  // Remove namespace for UI compatibility
  transports: ['polling', 'websocket'],
})
```

---

## 2. WebSocket Event Name Mismatches 🚨 CRITICAL

### Market Data Events

| Event Purpose       | UI Listens For  | Backend Emits   | Status      |
| ------------------- | --------------- | --------------- | ----------- |
| Single price update | `price_update`  | `quote`         | 🔴 MISMATCH |
| Bulk price update   | `prices_bulk`   | Not implemented | 🔴 MISSING  |
| Candle data         | `candle_update` | Not implemented | 🔴 MISSING  |
| Market regime       | `regime_update` | Not implemented | 🔴 MISSING  |

### Signal Aggregator Events (Working ✅)

| Event Purpose            | UI Listens For             | Backend Emits              | Status |
| ------------------------ | -------------------------- | -------------------------- | ------ |
| Prices                   | `prices`                   | `prices`                   | ✅ OK  |
| Trading update           | `trading_update`           | `trading_update`           | ✅ OK  |
| Worker assigned          | `worker_assigned`          | `worker_assigned`          | ✅ OK  |
| Worker thinking          | `worker_thinking`          | `worker_thinking`          | ✅ OK  |
| Trade marker             | `trade_marker`             | `trade_marker`             | ✅ OK  |
| Order status             | `order_status`             | `order_status`             | ✅ OK  |
| Position update          | `position_update`          | `position_update`          | ✅ OK  |
| Pipeline start           | `pipeline_start`           | `pipeline_start`           | ✅ OK  |
| Pipeline progress        | `pipeline_progress`        | `pipeline_progress`        | ✅ OK  |
| Pipeline complete        | `pipeline_complete`        | `pipeline_complete`        | ✅ OK  |
| Scheduler task started   | `scheduler_task_started`   | `scheduler_task_started`   | ✅ OK  |
| Scheduler task completed | `scheduler_task_completed` | `scheduler_task_completed` | ✅ OK  |
| System health            | `system_health`            | `system_health`            | ✅ OK  |
| Market status            | `market_status`            | `market_status`            | ✅ OK  |

### Stock Picker Events (via Market Data Socket)

| Event Purpose         | UI Listens For          | Backend Emits           | Status     |
| --------------------- | ----------------------- | ----------------------- | ---------- |
| Pipeline started      | `pipeline_started`      | `pipeline_started`      | ✅ OK      |
| Pipeline layer update | `pipeline_layer_update` | `pipeline_layer_update` | ✅ OK      |
| Pipeline progress     | `pipeline_progress`     | `pipeline_progress`     | ✅ OK      |
| Pipeline complete     | `pipeline_complete`     | `pipeline_complete`     | ✅ OK      |
| Pipeline error        | `pipeline_error`        | `pipeline_error`        | ✅ OK      |
| Stock picks           | `stock_picks`           | Not implemented         | 🔴 MISSING |
| Stock pick detail     | `stock_pick_detail`     | Not implemented         | 🔴 MISSING |

### Affected Files

**UI Side:**

- `ai/trading-ui/src/app/services/real-time.service.ts` (lines 520-560)

**Backend Side:**

- `ai/trading-platform/apps/market-data/src/gateways/market-data.gateway.ts`

### Fix Required

Add event name aliases in market-data gateway:

```typescript
broadcastQuote(quote: Quote) {
  // Emit both for backwards compatibility
  this.server.to(`symbol:${quote.symbol}`).emit('quote', quote);
  this.server.to(`symbol:${quote.symbol}`).emit('price_update', quote);  // ADD THIS
}
```

---

## 3. HTTP API Endpoint Analysis

### API Gateway (Port 3000) - TradingControlService

| Endpoint           | UI Expects                               | Backend Provides                         | Status     |
| ------------------ | ---------------------------------------- | ---------------------------------------- | ---------- |
| Emergency Stop     | `POST /api/system/emergency-stop`        | `POST /api/system/emergency-stop`        | ✅ OK      |
| Emergency Resume   | `POST /api/system/emergency-stop/resume` | `POST /api/system/emergency-stop/resume` | ✅ OK      |
| System Status      | `GET /api/system/status`                 | `GET /api/system/status`                 | ✅ OK      |
| Square Off Single  | `POST /api/positions/:symbol/square-off` | `POST /api/positions/:symbol/square-off` | ✅ OK      |
| Square Off All     | `POST /api/positions/square-off-all`     | `POST /api/positions/square-off-all`     | ✅ OK      |
| Square Off By Type | `POST /api/positions/square-off-by-type` | `POST /api/positions/square-off-by-type` | ✅ OK      |
| Trading Mode GET   | `GET /api/trading/mode`                  | `GET /api/trading/mode`                  | ✅ OK      |
| Trading Mode PUT   | `PUT /api/trading/mode`                  | `PUT /api/trading/mode`                  | ✅ OK      |
| Audit Logs         | `GET /api/audit-logs`                    | Not implemented                          | 🟡 MISSING |

### Signal Aggregator (Port 3002) - TradingService

| Endpoint           | UI Expects                 | Backend Provides           | Status |
| ------------------ | -------------------------- | -------------------------- | ------ |
| Status             | `GET /api/status`          | `GET /api/status`          | ✅ OK  |
| Signals            | `GET /api/signals`         | `GET /api/signals`         | ✅ OK  |
| Positions          | `GET /api/positions`       | `GET /api/positions`       | ✅ OK  |
| Prices             | `GET /api/prices`          | `GET /api/prices`          | ✅ OK  |
| Stats              | `GET /api/stats`           | `GET /api/stats`           | ✅ OK  |
| Trade              | `POST /api/trade`          | `POST /api/trade`          | ✅ OK  |
| Estimate Costs     | `POST /api/estimate-costs` | `POST /api/estimate-costs` | ✅ OK  |
| Watchlist          | `GET /api/watchlist`       | `GET /api/watchlist`       | ✅ OK  |
| Costs              | `GET /api/costs`           | `GET /api/costs`           | ✅ OK  |
| Orchestrator Start | `POST /orchestrator/start` | `POST /orchestrator/start` | ✅ OK  |
| Orchestrator Stop  | `POST /orchestrator/stop`  | `POST /orchestrator/stop`  | ✅ OK  |
| Groww Holdings     | `GET /api/groww/holdings`  | `GET /api/groww/holdings`  | ✅ OK  |
| Groww Orders       | `GET /api/groww/orders`    | `GET /api/groww/orders`    | ✅ OK  |
| Groww Margin       | `GET /api/groww/margin`    | `GET /api/groww/margin`    | ✅ OK  |
| Quote              | `GET /api/quote/:symbol`   | `GET /api/quote/:symbol`   | ✅ OK  |

### Signal Aggregator (Port 3002) - SchedulerService

| Endpoint        | UI Expects                            | Backend Provides                    | Status          |
| --------------- | ------------------------------------- | ----------------------------------- | --------------- |
| Dashboard       | `GET /scheduler/dashboard`            | `GET /scheduler/dashboard`          | ✅ OK           |
| Health          | `GET /scheduler/health`               | `GET /scheduler/health`             | ✅ OK           |
| Timeline        | `GET /scheduler/timeline`             | `GET /scheduler/timeline`           | ✅ OK           |
| Activities      | `GET /scheduler/activities`           | `GET /scheduler/activities`         | ✅ OK           |
| Stock Picks     | `GET /scheduler/stock-picks/latest`   | `GET /scheduler/stock-picks/latest` | ✅ OK           |
| Definitions     | `GET /scheduler/definitions`          | `GET /scheduler/registry`           | 🟡 PATH DIFFERS |
| Trigger Task    | `POST /eod/scheduler/trigger/:taskId` | Not verified                        | ⚠️ VERIFY       |
| Start Scheduler | `POST /eod/scheduler/start`           | Not verified                        | ⚠️ VERIFY       |
| Stop Scheduler  | `POST /eod/scheduler/stop`            | Not verified                        | ⚠️ VERIFY       |

### Trade Executor (Port 3005) - TradingService

| Endpoint | UI Expects    | Backend Provides | Status |
| -------- | ------------- | ---------------- | ------ |
| Trades   | `GET /trades` | `GET /trades`    | ✅ OK  |

---

## 4. Data Model Mismatches 🟡 WARNING

### Position Interface

**UI expects (`Position` interface):**

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

**Backend returns:**

```typescript
{
  symbol: string;
  quantity: number;
  avgPrice: number; // camelCase ❌
  currentPrice: number; // camelCase ❌
  unrealizedPnL: number; // Different name ❌
  // positionType: ✅ Added in api.controller.ts
}
```

**Fix Location:** `ai/trading-platform/apps/signal-aggregator/src/controllers/api.controller.ts` (line 282)
**Status:** ✅ Already transformed in `getPositions()` method

---

## 5. Service Port Configuration

| Service           | Expected Port | Configured Port | Status |
| ----------------- | ------------- | --------------- | ------ |
| API Gateway       | 3000          | 3000            | ✅ OK  |
| Market Data       | 3001          | 3001            | ✅ OK  |
| Signal Aggregator | 3002          | 3002            | ✅ OK  |
| Decision Tracker  | 3003          | 3003            | ✅ OK  |
| Portfolio Manager | 3004          | 3004            | ✅ OK  |
| Trade Executor    | 3005          | 3005            | ✅ OK  |

---

## 6. Priority Fix List

### 🔴 P0 - Critical (Blocking Real-Time Features)

1. **Market Data WebSocket Namespace**
   - File: `apps/market-data/src/gateways/market-data.gateway.ts`
   - Change: Remove `/market-data` namespace
   - Impact: Enables price updates in UI

2. **Market Data Event Names**
   - File: `apps/market-data/src/gateways/market-data.gateway.ts`
   - Change: Emit `price_update` alongside `quote`
   - Impact: UI receives real-time price updates

### 🟡 P1 - Important (Missing Features)

3. **Add Audit Logs Endpoint**
   - File: `apps/api-gateway/src/controllers/system.controller.ts`
   - Change: Add `GET /audit-logs` endpoint
   - Impact: Trading control audit trail

4. **Add Stock Picks WebSocket Events**
   - File: `apps/market-data/src/gateways/market-data.gateway.ts`
   - Change: Add `stock_picks` and `stock_pick_detail` emitters
   - Impact: Real-time stock picker updates

5. **Scheduler Definitions Path**
   - File: UI's `scheduler.service.ts` OR backend controller
   - Change: Align endpoint path (`/definitions` vs `/registry`)
   - Impact: Scheduler dashboard definitions

### 🟢 P2 - Nice to Have

6. **Bulk Price Events**
   - Add `prices_bulk` event to market-data gateway
   - Impact: Performance optimization for watchlists

7. **Candle/Regime Events**
   - Add `candle_update` and `regime_update` events
   - Impact: Chart and regime indicator updates

---

## 7. Recommended Action Plan

```
Week 1:
├── Day 1-2: Fix Market Data WebSocket namespace (P0 #1)
├── Day 3-4: Add event name aliases (P0 #2)
└── Day 5: Testing & validation

Week 2:
├── Day 1-2: Add Audit Logs endpoint (P1 #3)
├── Day 3-4: Add Stock Picks WebSocket events (P1 #4)
└── Day 5: Fix scheduler definitions path (P1 #5)

Week 3:
├── Day 1-3: Add P2 enhancements
└── Day 4-5: Integration testing
```

---

## 8. Testing Checklist

After fixes, verify:

- [ ] UI connects to Market Data WebSocket without errors
- [ ] Price updates appear in UI in real-time
- [ ] Trading signals flow from Signal Aggregator to UI
- [ ] Pipeline progress updates display correctly
- [ ] Worker tiles show live AI thinking logs
- [ ] Scheduler timeline updates in real-time
- [ ] Emergency stop activates and broadcasts to all clients
- [ ] Square-off operations reflect immediately in positions
- [ ] Audit logs display recent actions

---

## Appendix A: File References

### UI Services

| File                                  | Purpose                    |
| ------------------------------------- | -------------------------- |
| `services/real-time.service.ts`       | WebSocket connections      |
| `services/trading.service.ts`         | Trading HTTP API calls     |
| `services/trading-control.service.ts` | Emergency stop, square-off |
| `services/scheduler.service.ts`       | Scheduler HTTP API calls   |
| `services/health-polling.service.ts`  | Health check polling       |

### Backend Controllers

| File                                                              | Purpose                       |
| ----------------------------------------------------------------- | ----------------------------- |
| `api-gateway/controllers/system.controller.ts`                    | System status, emergency stop |
| `api-gateway/controllers/positions.controller.ts`                 | Square-off operations         |
| `api-gateway/controllers/trading.controller.ts`                   | Trading mode                  |
| `signal-aggregator/controllers/api.controller.ts`                 | Main trading API              |
| `signal-aggregator/controllers/scheduler-dashboard.controller.ts` | Scheduler API                 |

### Backend Gateways (WebSocket)

| File                                           | Purpose                  |
| ---------------------------------------------- | ------------------------ |
| `signal-aggregator/gateways/signal.gateway.ts` | Main real-time events    |
| `market-data/gateways/market-data.gateway.ts`  | Price & pipeline events  |
| `api-gateway/gateways/trading.gateway.ts`      | Trading events (unused?) |

---

_Report generated from CodeTrellis Matrix v1.0.0 analysis_
