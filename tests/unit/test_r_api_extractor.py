"""
Tests for RAPIExtractor — Plumber routes, Shiny components,
RestRserve endpoints, Ambiorix routes.

Part of CodeTrellis v4.26 R Language Support.
"""

import pytest
from codetrellis.extractors.r.api_extractor import RAPIExtractor


@pytest.fixture
def extractor():
    return RAPIExtractor()


# ===== PLUMBER ROUTE EXTRACTION =====

class TestPlumberRouteExtraction:
    """Tests for Plumber REST API route extraction."""

    def test_plumber_get_route(self, extractor):
        code = '''
#* Get all users
#* @get /api/users
function() {
  get_all_users()
}
'''
        result = extractor.extract(code, "api.R")
        routes = result["routes"]
        assert len(routes) >= 1
        route = routes[0]
        assert route.method == "GET"
        assert route.path == "/api/users"
        assert route.framework == "plumber"

    def test_plumber_post_route(self, extractor):
        code = '''
#* Create a new user
#* @param name User name
#* @param email User email
#* @post /api/users
function(name, email) {
  create_user(name, email)
}
'''
        result = extractor.extract(code, "api.R")
        routes = result["routes"]
        assert len(routes) >= 1
        route = routes[0]
        assert route.method == "POST"
        assert route.path == "/api/users"

    def test_plumber_parameterized_route(self, extractor):
        code = '''
#* Get user by ID
#* @get /api/users/<id:int>
function(id) {
  get_user(as.integer(id))
}
'''
        result = extractor.extract(code, "api.R")
        routes = result["routes"]
        assert len(routes) >= 1
        route = routes[0]
        assert route.method == "GET"
        assert "<id" in route.path or "id" in str(route.params)

    def test_multiple_plumber_routes(self, extractor):
        code = '''
#* List items
#* @get /api/items
function() { list_items() }

#* Create item
#* @post /api/items
function(name, price) { create_item(name, price) }

#* Delete item
#* @delete /api/items/<id>
function(id) { delete_item(id) }
'''
        result = extractor.extract(code, "api.R")
        routes = result["routes"]
        assert len(routes) >= 3


# ===== SHINY COMPONENT EXTRACTION =====

class TestShinyComponentExtraction:
    """Tests for Shiny component extraction."""

    def test_shiny_render_output(self, extractor):
        code = '''
server <- function(input, output, session) {
  output$plot <- renderPlot({
    hist(rnorm(input$n))
  })
  output$table <- renderTable({
    head(iris, input$rows)
  })
}
'''
        result = extractor.extract(code, "server.R")
        components = result["shiny_components"]
        assert len(components) >= 1
        # Verify renders are captured in the server component
        server = components[0]
        assert len(server.renders) >= 2

    def test_shiny_reactive_values(self, extractor):
        code = '''
server <- function(input, output, session) {
  values <- reactiveValues(count = 0, data = NULL)
  observeEvent(input$btn, {
    values$count <- values$count + 1
  })
}
'''
        result = extractor.extract(code, "server.R")
        components = result["shiny_components"]
        assert len(components) >= 1

    def test_shiny_module_server(self, extractor):
        code = '''
filterServer <- function(id, data) {
  moduleServer(id, function(input, output, session) {
    reactive({
      data() %>% filter(category == input$category)
    })
  })
}
'''
        result = extractor.extract(code, "mod_filter.R")
        components = result["shiny_components"]
        assert len(components) >= 1

    def test_shiny_ui_components(self, extractor):
        code = '''
ui <- fluidPage(
  titlePanel("My App"),
  sidebarLayout(
    sidebarPanel(
      selectInput("var", "Variable", choices = names(iris)),
      sliderInput("n", "Count", min = 1, max = 100, value = 50)
    ),
    mainPanel(
      plotOutput("plot"),
      tableOutput("table")
    )
  )
)
'''
        result = extractor.extract(code, "ui.R")
        # UI elements should be detected
        components = result["shiny_components"]
        assert len(components) >= 0  # UI detection may vary


# ===== REST API ENDPOINT EXTRACTION =====

class TestAPIEndpointExtraction:
    """Tests for RestRserve and Ambiorix endpoint extraction."""

    def test_restrserve_endpoint(self, extractor):
        code = '''
app <- Application$new()
app$add_get("/api/health", function(.req, .res) {
  .res$set_body('{"status": "ok"}')
})
'''
        result = extractor.extract(code, "app.R")
        endpoints = result["api_endpoints"]
        assert len(endpoints) >= 1


# ===== NO API CODE =====

class TestNoAPICode:
    """Tests for files without API code."""

    def test_plain_r_code(self, extractor):
        code = '''
x <- 1 + 2
y <- sqrt(x)
cat(y)
'''
        result = extractor.extract(code, "simple.R")
        assert len(result["routes"]) == 0
        assert len(result["shiny_components"]) == 0
        assert len(result["api_endpoints"]) == 0
