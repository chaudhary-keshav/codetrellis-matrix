"""
Tests for CSharpAPIExtractor — ASP.NET Core controllers, Minimal APIs, gRPC, SignalR.

Part of CodeTrellis v4.13 C# Language Support.
"""

import pytest
from codetrellis.extractors.csharp.api_extractor import CSharpAPIExtractor


@pytest.fixture
def extractor():
    return CSharpAPIExtractor()


# ===== CONTROLLER ENDPOINT EXTRACTION =====

class TestControllerEndpoints:
    """Tests for ASP.NET Core controller endpoint extraction."""

    def test_httpget_endpoint(self, extractor):
        code = '''
        [ApiController]
        [Route("api/[controller]")]
        public class UsersController : ControllerBase
        {
            [HttpGet]
            public IActionResult GetAll()
            {
                return Ok();
            }
        }
        '''
        result = extractor.extract(code, "UsersController.cs")
        assert len(result["endpoints"]) >= 1
        ep = result["endpoints"][0]
        assert ep.method == "GET"

    def test_httppost_with_route(self, extractor):
        code = '''
        [ApiController]
        [Route("api/orders")]
        public class OrdersController : ControllerBase
        {
            [HttpPost("create")]
            public async Task<IActionResult> CreateOrder([FromBody] CreateOrderRequest request)
            {
                return Ok();
            }
        }
        '''
        result = extractor.extract(code, "OrdersController.cs")
        assert len(result["endpoints"]) >= 1
        ep = result["endpoints"][0]
        assert ep.method == "POST"

    def test_multiple_endpoints(self, extractor):
        code = '''
        [ApiController]
        [Route("api/products")]
        public class ProductsController : ControllerBase
        {
            [HttpGet]
            public IActionResult GetAll() => Ok();

            [HttpGet("{id}")]
            public IActionResult GetById(int id) => Ok();

            [HttpPost]
            public IActionResult Create([FromBody] ProductDto dto) => Ok();

            [HttpPut("{id}")]
            public IActionResult Update(int id, [FromBody] ProductDto dto) => Ok();

            [HttpDelete("{id}")]
            public IActionResult Delete(int id) => Ok();
        }
        '''
        result = extractor.extract(code, "ProductsController.cs")
        assert len(result["endpoints"]) >= 4

    def test_authorized_endpoint(self, extractor):
        code = '''
        [ApiController]
        [Route("api/admin")]
        [Authorize(Policy = "AdminOnly")]
        public class AdminController : ControllerBase
        {
            [HttpGet]
            public IActionResult Dashboard() => Ok();
        }
        '''
        result = extractor.extract(code, "AdminController.cs")
        endpoints = result["endpoints"]
        # Controller-level Authorize should mark endpoints as authorized
        assert len(endpoints) >= 1


# ===== MINIMAL API EXTRACTION =====

class TestMinimalApiEndpoints:
    """Tests for .NET 6+ Minimal API endpoint extraction."""

    def test_basic_mapget(self, extractor):
        code = '''
        app.MapGet("/api/hello", () => "Hello World!");
        '''
        result = extractor.extract(code, "Program.cs")
        assert len(result["endpoints"]) >= 1
        ep = result["endpoints"][0]
        assert ep.method == "GET"
        assert ep.path == "/api/hello"
        assert ep.framework == "minimal_api"

    def test_mappost(self, extractor):
        code = '''
        app.MapPost("/api/orders", CreateOrderAsync);
        '''
        result = extractor.extract(code, "Program.cs")
        assert len(result["endpoints"]) >= 1
        ep = result["endpoints"][0]
        assert ep.method == "POST"
        assert ep.path == "/api/orders"
        assert ep.handler_method == "CreateOrderAsync"

    def test_map_group_endpoints(self, extractor):
        code = '''
        var api = app.MapGroup("api/orders").HasApiVersion(1.0);
        api.MapPut("/cancel", CancelOrderAsync);
        api.MapGet("{orderId:int}", GetOrderAsync);
        api.MapPost("/", CreateOrderAsync);
        api.MapDelete("/{id}", DeleteOrderAsync);
        '''
        result = extractor.extract(code, "OrdersApi.cs")
        assert len(result["endpoints"]) >= 4
        methods = {ep.method for ep in result["endpoints"]}
        assert "PUT" in methods
        assert "GET" in methods
        assert "POST" in methods
        assert "DELETE" in methods

    def test_mapget_with_named_handler(self, extractor):
        code = '''
        endpoints.MapGet("/items", GetAllItems);
        endpoints.MapGet("/items/{id}", GetItemById);
        '''
        result = extractor.extract(code, "ItemsApi.cs")
        assert len(result["endpoints"]) >= 2
        handlers = {ep.handler_method for ep in result["endpoints"]}
        assert "GetAllItems" in handlers
        assert "GetItemById" in handlers


# ===== GRPC SERVICE EXTRACTION =====

class TestGrpcServiceExtraction:
    """Tests for gRPC service detection."""

    def test_grpc_service(self, extractor):
        code = '''
        public class GreeterService : Greeter.GreeterBase
        {
            public override Task<HelloReply> SayHello(HelloRequest request, ServerCallContext context)
            {
                return Task.FromResult(new HelloReply { Message = "Hello " + request.Name });
            }
        }
        '''
        result = extractor.extract(code, "GreeterService.cs")
        assert len(result["grpc_services"]) >= 1
        svc = result["grpc_services"][0]
        assert svc.name == "GreeterService"

    def test_grpc_service_with_multiple_methods(self, extractor):
        code = '''
        public class BasketService : Basket.BasketBase
        {
            public override async Task<CustomerBasketResponse> GetBasket(GetBasketRequest request, ServerCallContext context)
            {
                return new CustomerBasketResponse();
            }
            public override async Task<CustomerBasketResponse> UpdateBasket(UpdateBasketRequest request, ServerCallContext context)
            {
                return new CustomerBasketResponse();
            }
        }
        '''
        result = extractor.extract(code, "BasketService.cs")
        assert len(result["grpc_services"]) >= 1


# ===== SIGNALR HUB EXTRACTION =====

class TestSignalRHubExtraction:
    """Tests for SignalR hub detection."""

    def test_signalr_hub(self, extractor):
        code = '''
        public class ChatHub : Hub
        {
            public async Task SendMessage(string user, string message)
            {
                await Clients.All.SendAsync("ReceiveMessage", user, message);
            }
        }
        '''
        result = extractor.extract(code, "ChatHub.cs")
        assert len(result["signalr_hubs"]) >= 1
        hub = result["signalr_hubs"][0]
        assert hub.name == "ChatHub"

    def test_typed_signalr_hub(self, extractor):
        code = '''
        public class NotificationHub : Hub<INotificationClient>
        {
            public async Task SendNotification(string title, string message)
            {
                await Clients.All.ReceiveNotification(title, message);
            }
        }
        '''
        result = extractor.extract(code, "NotificationHub.cs")
        assert len(result["signalr_hubs"]) >= 1
        hub = result["signalr_hubs"][0]
        assert hub.name == "NotificationHub"


# ===== RAZOR PAGE HANDLERS =====

class TestRazorPageHandlers:
    """Tests for Razor Page handler extraction."""

    def test_razor_page_handlers(self, extractor):
        code = '''
        public class IndexModel : PageModel
        {
            public void OnGet()
            {
            }

            public async Task<IActionResult> OnPostAsync()
            {
                return Page();
            }
        }
        '''
        result = extractor.extract(code, "Index.cshtml.cs")
        # Razor pages produce endpoints
        assert len(result["endpoints"]) >= 1
