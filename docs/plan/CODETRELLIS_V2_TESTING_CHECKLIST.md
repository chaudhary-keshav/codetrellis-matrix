# CodeTrellis v2.0 - Testing Checklist

**Version:** 1.0.0
**Created:** 31 January 2026

---

## 🧪 Testing Overview

This document contains the complete testing checklist for CodeTrellis v2.0 implementation.

### Testing Pyramid

```
                    ┌─────────────┐
                    │    E2E      │  ~10%
                    │   Tests     │
                    ├─────────────┤
                    │ Integration │  ~20%
                    │   Tests     │
                    ├─────────────┤
                    │             │
                    │    Unit     │  ~70%
                    │   Tests     │
                    │             │
                    └─────────────┘
```

---

## ✅ Unit Tests Checklist

### 1. Interface Parser (`test_interface_parser.py`)

#### Basic Interface Extraction

- [ ] **T1.1** Parse simple interface with primitive types

  ```typescript
  interface User {
    name: string;
    age: number;
  }
  ```

  Expected: `User{name:string,age:number}`

- [ ] **T1.2** Parse interface with optional properties

  ```typescript
  interface Config {
    host: string;
    port?: number;
  }
  ```

  Expected: `Config{host:string!,port?:number}`

- [ ] **T1.3** Parse interface with readonly properties

  ```typescript
  interface Point {
    readonly x: number;
    readonly y: number;
  }
  ```

  Expected: `Point{x:number!readonly,y:number!readonly}`

- [ ] **T1.4** Parse interface extending another interface
  ```typescript
  interface Employee extends Person {
    salary: number;
  }
  ```
  Expected: `Employee extends Person{salary:number}`

#### Complex Interface Extraction

- [ ] **T1.5** Parse nested interface

  ```typescript
  interface Order {
    item: { name: string; price: number };
    quantity: number;
  }
  ```

  Expected: `Order{item:{name:string,price:number},quantity:number}`

- [ ] **T1.6** Parse interface with array types

  ```typescript
  interface Cart {
    items: Product[];
    total: number;
  }
  ```

  Expected: `Cart{items:Product[],total:number}`

- [ ] **T1.7** Parse interface with generic types

  ```typescript
  interface Response<T> {
    data: T;
    error: string | null;
  }
  ```

  Expected: `Response<T>{data:T,error:string|null}`

- [ ] **T1.8** Parse interface with Record/Map types

  ```typescript
  interface Cache {
    entries: Record<string, CacheEntry>;
  }
  ```

  Expected: `Cache{entries:Record<string,CacheEntry>}`

- [ ] **T1.9** Parse interface with function types

  ```typescript
  interface Handler {
    onSuccess: (data: Data) => void;
  }
  ```

  Expected: `Handler{onSuccess:(data:Data)=>void}`

- [ ] **T1.10** Parse multiple interfaces in same file
  ```typescript
  interface A {
    x: number;
  }
  interface B {
    y: string;
  }
  ```
  Expected: Both interfaces captured

---

### 2. Type Parser (`test_type_parser.py`)

#### Basic Type Aliases

- [ ] **T2.1** Parse simple type alias

  ```typescript
  type ID = string;
  ```

  Expected: `ID=string`

- [ ] **T2.2** Parse union type

  ```typescript
  type Status = 'active' | 'inactive' | 'pending';
  ```

  Expected: `Status='active'|'inactive'|'pending'`

- [ ] **T2.3** Parse intersection type

  ```typescript
  type Employee = Person & { department: string };
  ```

  Expected: `Employee=Person&{department:string}`

- [ ] **T2.4** Parse literal type
  ```typescript
  type Direction = 'up' | 'down' | 'left' | 'right';
  ```
  Expected: `Direction='up'|'down'|'left'|'right'`

#### Complex Type Aliases

- [ ] **T2.5** Parse generic type alias

  ```typescript
  type Nullable<T> = T | null;
  ```

  Expected: `Nullable<T>=T|null`

- [ ] **T2.6** Parse conditional type

  ```typescript
  type NonNullable<T> = T extends null ? never : T;
  ```

  Expected: `NonNullable<T>=T extends null?never:T`

- [ ] **T2.7** Parse mapped type

  ```typescript
  type Readonly<T> = { readonly [K in keyof T]: T[K] };
  ```

  Expected: `Readonly<T>={readonly[K in keyof T]:T[K]}`

- [ ] **T2.8** Parse tuple type
  ```typescript
  type Coordinate = [number, number];
  ```
  Expected: `Coordinate=[number,number]`

---

### 3. Component Parser (`test_component_parser.py`)

#### Basic Component Extraction

- [ ] **T3.1** Parse component name and selector

  ```typescript
  @Component({ selector: 'app-user' })
  export class UserComponent {}
  ```

  Expected: `UserComponent|selector:app-user`

- [ ] **T3.2** Parse standalone component

  ```typescript
  @Component({ standalone: true })
  ```

  Expected: `type=component|standalone`

- [ ] **T3.3** Parse OnPush change detection
  ```typescript
  @Component({ changeDetection: ChangeDetectionStrategy.OnPush })
  ```
  Expected: `type=component|OnPush`

#### Input Extraction

- [ ] **T3.4** Parse old @Input decorator

  ```typescript
  @Input() title: string;
  ```

  Expected: `[INPUTS] title:string`

- [ ] **T3.5** Parse new input() signal

  ```typescript
  readonly title = input<string>('default');
  ```

  Expected: `[INPUTS] title:string='default'`

- [ ] **T3.6** Parse required input

  ```typescript
  readonly data = input.required<Data>();
  ```

  Expected: `[INPUTS] data:Data=required`

- [ ] **T3.7** Parse input with transform
  ```typescript
  readonly count = input(0, { transform: numberAttribute });
  ```
  Expected: `[INPUTS] count:number=0|transform:numberAttribute`

#### Output Extraction

- [ ] **T3.8** Parse old @Output decorator

  ```typescript
  @Output() clicked = new EventEmitter<MouseEvent>();
  ```

  Expected: `[OUTPUTS] clicked:EventEmitter<MouseEvent>`

- [ ] **T3.9** Parse new output() signal
  ```typescript
  readonly saved = output<SaveEvent>();
  ```
  Expected: `[OUTPUTS] saved:OutputEmitter<SaveEvent>`

#### Signal Extraction

- [ ] **T3.10** Parse signal with initial value

  ```typescript
  readonly count = signal(0);
  ```

  Expected: `[SIGNALS] count:WritableSignal<number>=0`

- [ ] **T3.11** Parse signal with type annotation
  ```typescript
  readonly items = signal<Item[]>([]);
  ```
  Expected: `[SIGNALS] items:WritableSignal<Item[]>=[]`

#### Computed Signal Extraction

- [ ] **T3.12** Parse simple computed

  ```typescript
  readonly double = computed(() => this.count() * 2);
  ```

  Expected: `[COMPUTED] double=computed(count*2)`

- [ ] **T3.13** Parse computed with multiple dependencies

  ```typescript
  readonly total = computed(() => this.price() * this.quantity());
  ```

  Expected: `[COMPUTED] total=computed(price*quantity)`

- [ ] **T3.14** Parse computed from store
  ```typescript
  readonly items = computed(() => this.store.items());
  ```
  Expected: `[COMPUTED] items=computed(store.items)`

#### Method Extraction

- [ ] **T3.15** Parse public methods

  ```typescript
  refresh(): void { }
  calculate(a: number, b: number): number { }
  ```

  Expected: `[METHODS] refresh():void,calculate(a:number,b:number):number`

- [ ] **T3.16** Exclude private methods
  ```typescript
  private internalMethod(): void { }
  ```
  Expected: Not included in output

#### Dependency Injection Extraction

- [ ] **T3.17** Parse inject() calls

  ```typescript
  private readonly service = inject(TradingService);
  ```

  Expected: `[DEPS] TradingService`

- [ ] **T3.18** Parse constructor injection
  ```typescript
  constructor(private service: TradingService) {}
  ```
  Expected: `[DEPS] TradingService`

---

### 4. SignalStore Parser (`test_store_parser.py`)

#### State Extraction

- [ ] **T4.1** Parse withState interface

  ```typescript
  interface State {
    items: Item[];
    loading: boolean;
  }
  withState<State>({ items: [], loading: false });
  ```

  Expected: `[STATE] items:Item[]=[],loading:boolean=false`

- [ ] **T4.2** Parse inline state
  ```typescript
  withState({ count: 0, name: '' });
  ```
  Expected: `[STATE] count:number=0,name:string=''`

#### Computed Extraction

- [ ] **T4.3** Parse withComputed selectors
  ```typescript
  withComputed((state) => ({
    itemCount: computed(() => state.items().length),
    isEmpty: computed(() => state.items().length === 0),
  }));
  ```
  Expected: `[COMPUTED] itemCount=computed(items.length),isEmpty=computed(items.length===0)`

#### Methods Extraction

- [ ] **T4.4** Parse withMethods

  ```typescript
  withMethods((store) => ({
    addItem(item: Item): void {},
    removeItem(id: string): void {},
  }));
  ```

  Expected: `[METHODS] addItem(item:Item):void,removeItem(id:string):void`

- [ ] **T4.5** Parse patchState usage
  ```typescript
  setLoading(loading: boolean): void {
    patchState(store, { loading });
  }
  ```
  Expected: `[METHODS] setLoading(loading:boolean):void`

---

### 5. Route Parser (`test_route_parser.py`)

#### Basic Route Extraction

- [ ] **T5.1** Parse simple route

  ```typescript
  { path: 'dashboard', component: DashboardComponent }
  ```

  Expected: `/dashboard→DashboardComponent`

- [ ] **T5.2** Parse route with redirect

  ```typescript
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' }
  ```

  Expected: `/→redirect:/dashboard`

- [ ] **T5.3** Parse route with parameters
  ```typescript
  { path: 'user/:id', component: UserComponent }
  ```
  Expected: `/user/:id→UserComponent|params:id`

#### Complex Route Extraction

- [ ] **T5.4** Parse child routes

  ```typescript
  {
    path: 'admin',
    component: AdminLayout,
    children: [
      { path: 'users', component: UsersComponent },
      { path: 'settings', component: SettingsComponent },
    ]
  }
  ```

  Expected:

  ```
  /admin→AdminLayout|children
    /admin/users→UsersComponent
    /admin/settings→SettingsComponent
  ```

- [ ] **T5.5** Parse lazy-loaded routes

  ```typescript
  {
    path: 'reports',
    loadChildren: () => import('./reports/routes').then(m => m.ROUTES)
  }
  ```

  Expected: `/reports→lazy:./reports/routes`

- [ ] **T5.6** Parse route guards
  ```typescript
  {
    path: 'admin',
    component: AdminComponent,
    canActivate: [AuthGuard, AdminGuard]
  }
  ```
  Expected: `/admin→AdminComponent|guards:AuthGuard,AdminGuard`

---

### 6. WebSocket Parser (`test_websocket_parser.py`)

#### Event Listening Extraction

- [ ] **T6.1** Parse socket.on() events

  ```typescript
  this.socket.on('trading_update', (data) => {});
  ```

  Expected: `[EVENTS:IN] trading_update`

- [ ] **T6.2** Parse socket.on() with typed payload
  ```typescript
  this.socket.on('price_update', (data: PriceData) => {});
  ```
  Expected: `[EVENTS:IN] price_update:PriceData`

#### Event Emission Extraction

- [ ] **T6.3** Parse socket.emit() events

  ```typescript
  this.socket.emit('subscribe', { symbols: ['AAPL'] });
  ```

  Expected: `[EVENTS:OUT] subscribe`

- [ ] **T6.4** Parse emit with typed payload
  ```typescript
  this.socket.emit('order', order as OrderPayload);
  ```
  Expected: `[EVENTS:OUT] order:OrderPayload`

---

### 7. HTTP API Parser (`test_api_parser.py`)

#### HTTP Method Extraction

- [ ] **T7.1** Parse GET request

  ```typescript
  this.http.get<User[]>('/api/users');
  ```

  Expected: `[API] GET:/api/users→User[]`

- [ ] **T7.2** Parse POST request

  ```typescript
  this.http.post<Order>('/api/orders', orderData);
  ```

  Expected: `[API] POST:/api/orders→Order`

- [ ] **T7.3** Parse request with template URL

  ```typescript
  this.http.get(`/api/users/${id}`);
  ```

  Expected: `[API] GET:/api/users/:id`

- [ ] **T7.4** Parse request with base URL
  ```typescript
  private baseUrl = 'http://localhost:3000';
  this.http.get(`${this.baseUrl}/api/health`);
  ```
  Expected: `[API] GET:http://localhost:3000/api/health`

---

## ✅ Integration Tests Checklist

### 8. Scanner Integration (`test_scanner_integration.py`)

- [ ] **T8.1** Scan folder with multiple component files
- [ ] **T8.2** Scan folder with component + service + store
- [ ] **T8.3** Scan folder and extract all dependencies
- [ ] **T8.4** Scan folder and link interfaces to components
- [ ] **T8.5** Handle circular dependencies gracefully
- [ ] **T8.6** Skip ignored files/folders correctly
- [ ] **T8.7** Generate correct file structure

### 9. Formatter Integration (`test_formatter_integration.py`)

- [ ] **T9.1** Format component with all sections
- [ ] **T9.2** Format store with state/computed/methods
- [ ] **T9.3** Format service with API/events/deps
- [ ] **T9.4** Format routes file
- [ ] **T9.5** V2.0 format is valid and parseable
- [ ] **T9.6** V1.0 compatibility - read old format
- [ ] **T9.7** V1.0 compatibility - upgrade to V2.0

### 10. Distributed Generator Integration (`test_generator_integration.py`)

- [ ] **T10.1** Generate .codetrellis in each component folder
- [ ] **T10.2** Generate .codetrellis for stores folder
- [ ] **T10.3** Generate .codetrellis for services folder
- [ ] **T10.4** Skip folders without relevant files
- [ ] **T10.5** Handle nested folder structures
- [ ] **T10.6** Idempotent generation (same input = same output)

---

## ✅ End-to-End Tests Checklist

### 11. CLI E2E (`test_cli_e2e.py`)

- [ ] **T11.1** `codetrellis scan <path>` generates matrix.prompt
- [ ] **T11.2** .codetrellis distribute <path>` generates .codetrellis files
- [ ] **T11.3** `codetrellis show <path>` displays compressed output
- [ ] **T11.4** `codetrellis init <path>` creates .codetrellis directory
- [ ] **T11.5** .codetrellis validate <path>` reports validation errors
- [ ] **T11.6** .codetrellis upgrade <path>` upgrades V1→V2

### 12. Full Project E2E (`test_project_e2e.py`)

- [ ] **T12.1** Scan entire trading-ui project
- [ ] **T12.2** Verify all 70+ components parsed
- [ ] **T12.3** Verify all 11 stores parsed
- [ ] **T12.4** Verify all routes extracted
- [ ] **T12.5** Verify all interfaces extracted
- [ ] **T12.6** Compare output with expected baseline
- [ ] **T12.7** No regressions from V1.0 output

---

## ✅ Regression Tests Checklist

### 13. V1.0 Compatibility (`test_v1_compatibility.py`)

- [ ] **T13.1** Read existing V1.0 .codetrellis files without error
- [ ] **T13.2** Upgrade preserves all V1.0 information
- [ ] **T13.3** No data loss during upgrade
- [ ] **T13.4** V1.0 format still writable with --format=v1
- [ ] **T13.5** Mixed V1/V2 files in same project works

---

## 📊 Test Coverage Requirements

| Module           | Minimum Coverage |
| ---------------- | ---------------- |
| Interface Parser | 95%              |
| Type Parser      | 95%              |
| Component Parser | 95%              |
| Store Parser     | 95%              |
| Route Parser     | 95%              |
| WebSocket Parser | 90%              |
| API Parser       | 90%              |
| Scanner          | 90%              |
| Formatter        | 90%              |
| CLI              | 85%              |
| **Overall**      | **90%**          |

---

## 🏃 Running Tests

```bash
# Run all tests
cd tools.codetrellis
pytest tests/ -v

# Run with coverage
pytest tests/ --cov.codetrellis --cov-report=html

# Run specific test file
pytest tests/unit/test_interface_parser.py -v

# Run specific test
pytest tests/unit/test_interface_parser.py::test_simple_interface -v

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run only e2e tests
pytest tests/e2e/ -v
```

---

## ✅ Pre-Merge Checklist

Before merging v2.0 branch:

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All e2e tests passing
- [ ] All regression tests passing
- [ ] Coverage >= 90%
- [ ] No linting errors
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version bumped to 2.0.0

---

**End of Testing Checklist**
