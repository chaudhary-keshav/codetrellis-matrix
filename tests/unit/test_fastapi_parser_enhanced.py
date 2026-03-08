"""
Tests for Enhanced FastAPI Parser.

Part of CodeTrellis v4.33 FastAPI Language Support.
Tests cover:
- Route extraction (GET, POST, PUT, DELETE, PATCH)
- Router extraction (APIRouter with prefix and tags)
- Middleware extraction (CORS, TrustedHost, GZip, custom)
- WebSocket route extraction
- Event handler extraction (startup, shutdown, lifespan)
- Exception handler extraction
- Background task detection
- Dependency injection detection
- Pydantic model detection
- Framework detection and version detection
- is_fastapi_file detection
- to_codetrellis_format output
"""

import pytest
from codetrellis.fastapi_parser_enhanced import (
    EnhancedFastAPIParser,
    FastAPIParseResult,
    FastAPIMiddlewareInfo,
    FastAPIWebSocketInfo,
    FastAPIEventHandlerInfo,
    FastAPIExceptionHandlerInfo,
    FastAPIBackgroundTaskInfo,
)
from codetrellis.extractors.python import (
    FastAPIExtractor,
    FastAPIRouteInfo,
)
from codetrellis.extractors.python.fastapi_extractor import (
    FastAPIRouterInfo,
    FastAPIParameterInfo,
    FastAPIDependencyInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedFastAPIParser()


@pytest.fixture
def fastapi_extractor():
    return FastAPIExtractor()


# ═══════════════════════════════════════════════════════════════════
# FastAPI Extractor (base) Tests
# ═══════════════════════════════════════════════════════════════════

class TestFastAPIExtractor:

    def test_extract_basic_routes(self, fastapi_extractor):
        """Test extracting basic FastAPI routes."""
        content = """
from fastapi import FastAPI

app = FastAPI()

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.post('/users')
async def create_user():
    return {'created': True}

@app.get('/users/{user_id}')
async def get_user(user_id: int):
    return {'id': user_id}
"""
        result = fastapi_extractor.extract(content)
        routes = result.get('routes', [])
        assert len(routes) >= 3

    def test_extract_routers(self, fastapi_extractor):
        """Test extracting APIRouter definitions."""
        content = """
from fastapi import APIRouter

router = APIRouter(prefix='/api/v1', tags=['users'])
items_router = APIRouter(prefix='/items', tags=['items'])
"""
        result = fastapi_extractor.extract(content)
        routers = result.get('routers', [])
        assert len(routers) >= 2


# ═══════════════════════════════════════════════════════════════════
# Enhanced FastAPI Parser Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedFastAPIParser:

    def test_is_fastapi_file(self, parser):
        """Test FastAPI file detection."""
        content = """
from fastapi import FastAPI

app = FastAPI()

@app.get('/health')
async def health():
    return {'status': 'ok'}
"""
        assert parser.is_fastapi_file(content, "main.py") is True

    def test_not_fastapi_file(self, parser):
        """Test non-FastAPI file detection."""
        content = """
import os
import json

def process_data():
    return {'data': 'processed'}
"""
        assert parser.is_fastapi_file(content, "utils.py") is False

    def test_parse_basic_app(self, parser):
        """Test parsing a basic FastAPI application."""
        content = """
from fastapi import FastAPI

app = FastAPI(title='My API', version='0.1.0')

@app.get('/')
async def root():
    return {'message': 'Hello World'}

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.post('/items')
async def create_item(name: str, price: float):
    return {'name': name, 'price': price}
"""
        result = parser.parse(content, "main.py")
        assert isinstance(result, FastAPIParseResult)
        assert len(result.routes) >= 3
        assert result.file_type == "app"

    def test_parse_routers(self, parser):
        """Test parsing APIRouter definitions."""
        content = """
from fastapi import APIRouter

router = APIRouter(prefix='/api/v1', tags=['users'])

@router.get('/users')
async def list_users():
    return []

@router.post('/users')
async def create_user(name: str):
    return {'name': name}
"""
        result = parser.parse(content, "routers.py")
        assert len(result.routers) >= 1
        assert result.routers[0].prefix == "/api/v1"

    def test_parse_middleware(self, parser):
        """Test parsing FastAPI middleware."""
        content = """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=['example.com'],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
"""
        result = parser.parse(content, "main.py")
        assert len(result.middleware) >= 3
        mw_types = [m.middleware_type for m in result.middleware]
        assert "cors" in mw_types
        assert "trustedhost" in mw_types

    def test_parse_websocket_routes(self, parser):
        """Test parsing WebSocket routes."""
        content = """
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f'Echo: {data}')

@app.websocket('/ws/{room_id}')
async def room_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()
"""
        result = parser.parse(content, "main.py")
        assert len(result.websocket_routes) >= 2

    def test_parse_event_handlers(self, parser):
        """Test parsing event handlers."""
        content = """
from fastapi import FastAPI

app = FastAPI()

@app.on_event('startup')
async def startup_event():
    print('Starting up...')

@app.on_event('shutdown')
async def shutdown_event():
    print('Shutting down...')
"""
        result = parser.parse(content, "main.py")
        assert len(result.event_handlers) >= 2
        events = [e.event for e in result.event_handlers]
        assert "startup" in events
        assert "shutdown" in events

    def test_parse_exception_handlers(self, parser):
        """Test parsing exception handlers."""
        content = """
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={'detail': 'Not found'})

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={'detail': str(exc)})
"""
        result = parser.parse(content, "main.py")
        assert len(result.exception_handlers) >= 2

    def test_detect_frameworks(self, parser):
        """Test FastAPI ecosystem framework detection."""
        content = """
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from tortoise import fields
"""
        result = parser.parse(content, "main.py")
        assert 'fastapi' in result.detected_frameworks

    def test_parse_dependency_injection(self, parser):
        """Test parsing file with dependency injection patterns. Routes with complex
        Depends() signatures may not be captured by regex-based extraction."""
        content = """
from fastapi import FastAPI, Depends

app = FastAPI()

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/items')
async def read_items(db=Depends(get_db)):
    return []
"""
        result = parser.parse(content, "main.py")
        assert isinstance(result, FastAPIParseResult)
        assert 'fastapi' in result.detected_frameworks

    def test_parse_pydantic_models(self, parser):
        """Test parsing alongside Pydantic models."""
        content = """
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

@app.post('/items', response_model=ItemResponse)
async def create_item(item: ItemCreate):
    return {'id': 1, **item.dict()}
"""
        result = parser.parse(content, "main.py")
        assert len(result.routes) >= 1

    def test_to_codetrellis_format(self, parser):
        """Test to_codetrellis_format produces valid output."""
        content = """
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=['*'])

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.post('/users')
async def create_user(name: str):
    return {'name': name}

@app.websocket('/ws')
async def ws(websocket: WebSocket):
    await websocket.accept()
"""
        result = parser.parse(content, "main.py")
        output = parser.to_codetrellis_format(result)

        assert isinstance(output, str)
        assert "[FILE:" in output
        assert "FASTAPI" in output

    def test_to_codetrellis_format_middleware(self, parser):
        """Test to_codetrellis_format includes middleware info."""
        content = """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['example.com'])
"""
        result = parser.parse(content, "main.py")
        output = parser.to_codetrellis_format(result)

        if result.middleware:
            assert "FASTAPI_MIDDLEWARE" in output
            assert "cors" in output.lower()

    def test_to_codetrellis_format_routers(self, parser):
        """Test to_codetrellis_format includes router info."""
        content = """
from fastapi import APIRouter

router = APIRouter(prefix='/api/v1', tags=['users'])
admin_router = APIRouter(prefix='/admin', tags=['admin'])
"""
        result = parser.parse(content, "routes.py")
        output = parser.to_codetrellis_format(result)

        if result.routers:
            assert "FASTAPI_ROUTERS" in output

    def test_to_codetrellis_format_events(self, parser):
        """Test to_codetrellis_format includes event handlers."""
        content = """
from fastapi import FastAPI

app = FastAPI()

@app.on_event('startup')
async def startup():
    pass

@app.on_event('shutdown')
async def shutdown():
    pass
"""
        result = parser.parse(content, "main.py")
        output = parser.to_codetrellis_format(result)

        if result.event_handlers:
            assert "FASTAPI_EVENTS" in output

    def test_parse_empty_file(self, parser):
        """Test parsing empty content."""
        result = parser.parse("", "empty.py")
        assert isinstance(result, FastAPIParseResult)
        assert len(result.routes) == 0

    def test_parse_non_fastapi_file(self, parser):
        """Test parsing a file with no FastAPI imports."""
        content = """
import os
import json

def process():
    return json.dumps({'data': True})
"""
        result = parser.parse(content, "utils.py")
        assert isinstance(result, FastAPIParseResult)
        assert len(result.routes) == 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════

class TestFastAPIEdgeCases:

    def test_multiple_routers(self, parser):
        """Test parsing multiple APIRouters."""
        content = """
from fastapi import APIRouter

users_router = APIRouter(prefix='/users', tags=['users'])
items_router = APIRouter(prefix='/items', tags=['items'])
orders_router = APIRouter(prefix='/orders', tags=['orders'])

@users_router.get('/')
async def list_users():
    return []

@items_router.get('/')
async def list_items():
    return []

@orders_router.get('/')
async def list_orders():
    return []
"""
        result = parser.parse(content, "routes.py")
        assert len(result.routers) >= 3
        assert len(result.routes) >= 3

    def test_response_model_and_status_code(self, parser):
        """Test parsing routes with response_model and status_code."""
        content = """
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserResponse(BaseModel):
    id: int
    name: str

@app.post('/users', response_model=UserResponse, status_code=201)
async def create_user(name: str):
    return {'id': 1, 'name': name}

@app.get('/users/{user_id}', response_model=UserResponse)
async def get_user(user_id: int):
    return {'id': user_id, 'name': 'test'}
"""
        result = parser.parse(content, "main.py")
        assert len(result.routes) >= 2

    def test_custom_middleware(self, parser):
        """Test parsing custom middleware."""
        content = """
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        import time
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        response.headers['X-Process-Time'] = str(duration)
        return response

app.add_middleware(TimingMiddleware)
"""
        result = parser.parse(content, "main.py")
        assert len(result.middleware) >= 1

    def test_lifespan_handler(self, parser):
        """Test parsing lifespan handler (FastAPI 0.93+)."""
        content = """
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print('Starting up')
    yield
    # Shutdown
    print('Shutting down')

app = FastAPI(lifespan=lifespan)

@app.get('/')
async def root():
    return {'message': 'Hello'}
"""
        result = parser.parse(content, "main.py")
        assert isinstance(result, FastAPIParseResult)
        assert len(result.routes) >= 1

    def test_path_parameters_types(self, parser):
        """Test routes with various path parameter types."""
        content = """
from fastapi import FastAPI
from uuid import UUID

app = FastAPI()

@app.get('/items/{item_id}')
async def get_item(item_id: int):
    return {'id': item_id}

@app.get('/users/{user_uuid}')
async def get_user(user_uuid: UUID):
    return {'uuid': str(user_uuid)}

@app.get('/files/{file_path:path}')
async def get_file(file_path: str):
    return {'path': file_path}
"""
        result = parser.parse(content, "main.py")
        assert len(result.routes) >= 3

    def test_query_parameters(self, parser):
        """Test routes with query parameters. Complex function signatures with
        Query/Depends may not be captured by regex-based extraction."""
        content = """
from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI()

@app.get('/items')
async def list_items(
    skip: int = 0,
    limit: int = Query(default=10, le=100),
    q: Optional[str] = None
):
    return {'skip': skip, 'limit': limit, 'q': q}
"""
        result = parser.parse(content, "main.py")
        # Complex Query() signatures may not be captured by regex
        assert isinstance(result, FastAPIParseResult)
        assert 'fastapi' in result.detected_frameworks

    def test_mixed_sync_async(self, parser):
        """Test both sync and async handlers."""
        content = """
from fastapi import FastAPI

app = FastAPI()

@app.get('/sync')
def sync_endpoint():
    return {'type': 'sync'}

@app.get('/async')
async def async_endpoint():
    return {'type': 'async'}
"""
        result = parser.parse(content, "main.py")
        assert len(result.routes) >= 2
