"""
Tests for EnhancedRParser — comprehensive R parser integration tests.

Part of CodeTrellis v4.26 R Language Support.
"""

import pytest
from codetrellis.r_parser_enhanced import EnhancedRParser, RParseResult


@pytest.fixture
def parser():
    return EnhancedRParser()


# ===== BASIC PARSING =====

class TestBasicParsing:
    """Tests for basic R parsing."""

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.R")
        assert isinstance(result, RParseResult)
        assert result.file_path == "empty.R"
        assert len(result.classes) == 0
        assert len(result.functions) == 0

    def test_whitespace_only(self, parser):
        result = parser.parse("   \n\n  ", "blank.R")
        assert isinstance(result, RParseResult)
        assert len(result.classes) == 0

    def test_simple_r_code(self, parser):
        code = '''
add <- function(x, y) x + y
subtract <- function(x, y) x - y
'''
        result = parser.parse(code, "math.R")
        assert len(result.functions) >= 2
        names = [f.name for f in result.functions]
        assert "add" in names
        assert "subtract" in names


# ===== IMPORT DETECTION =====

class TestImportDetection:
    """Tests for library/require import detection."""

    def test_library_calls(self, parser):
        code = '''
library(dplyr)
library(ggplot2)
library(tidyr)
'''
        result = parser.parse(code, "script.R")
        assert "dplyr" in result.imports
        assert "ggplot2" in result.imports
        assert "tidyr" in result.imports

    def test_require_calls(self, parser):
        code = '''
require(data.table)
require(jsonlite)
'''
        result = parser.parse(code, "script.R")
        assert "data.table" in result.imports
        assert "jsonlite" in result.imports

    def test_namespace_imports(self, parser):
        code = '''
result <- purrr::map(x, sqrt)
info <- rlang::inform("message")
'''
        result = parser.parse(code, "script.R")
        assert "purrr" in result.imports
        assert "rlang" in result.imports

    def test_no_duplicate_imports(self, parser):
        code = '''
library(dplyr)
library(dplyr)
x <- dplyr::filter(data, x > 0)
'''
        result = parser.parse(code, "script.R")
        assert result.imports.count("dplyr") == 1


# ===== FRAMEWORK DETECTION =====

class TestFrameworkDetection:
    """Tests for R framework detection."""

    def test_detect_shiny(self, parser):
        code = '''
library(shiny)
ui <- fluidPage(
  plotOutput("plot")
)
server <- function(input, output, session) {
  output$plot <- renderPlot({ hist(rnorm(100)) })
}
shinyApp(ui, server)
'''
        result = parser.parse(code, "app.R")
        assert "shiny" in result.detected_frameworks

    def test_detect_plumber(self, parser):
        code = '''
#* @get /api/health
function() {
  list(status = "ok")
}
'''
        result = parser.parse(code, "plumber.R")
        assert "plumber" in result.detected_frameworks

    def test_detect_tidyverse(self, parser):
        code = '''
library(tidyverse)
data %>%
  filter(x > 0) %>%
  mutate(y = x * 2) %>%
  summarize(total = sum(y))
'''
        result = parser.parse(code, "analysis.R")
        assert "tidyverse" in result.detected_frameworks or "dplyr" in result.detected_frameworks

    def test_detect_data_table(self, parser):
        code = '''
library(data.table)
dt <- fread("data.csv")
result <- dt[status == "active", .(count = .N), by = region]
'''
        result = parser.parse(code, "dt.R")
        assert "data.table" in result.detected_frameworks

    def test_detect_ggplot2(self, parser):
        code = '''
ggplot(data, aes(x = date, y = value)) +
  geom_line() +
  theme_minimal()
'''
        result = parser.parse(code, "plot.R")
        assert "ggplot2" in result.detected_frameworks

    def test_detect_r6(self, parser):
        code = '''
MyClass <- R6::R6Class("MyClass",
  public = list(
    initialize = function() {}
  )
)
'''
        result = parser.parse(code, "class.R")
        assert "R6" in result.detected_frameworks

    def test_detect_testthat(self, parser):
        code = '''
test_that("addition works", {
  expect_equal(1 + 1, 2)
  expect_true(is.numeric(1))
})
'''
        result = parser.parse(code, "test.R")
        assert "testthat" in result.detected_frameworks

    def test_detect_dbi(self, parser):
        code = '''
con <- DBI::dbConnect(RSQLite::SQLite(), "my.db")
result <- DBI::dbGetQuery(con, "SELECT * FROM users")
DBI::dbDisconnect(con)
'''
        result = parser.parse(code, "db.R")
        assert "DBI" in result.detected_frameworks

    def test_detect_targets(self, parser):
        code = '''
library(targets)
list(
  tar_target(raw_data, read_csv("data.csv")),
  tar_target(clean, clean_data(raw_data)),
  tar_target(model, fit_model(clean))
)
'''
        result = parser.parse(code, "_targets.R")
        assert "targets" in result.detected_frameworks

    def test_detect_roxygen2(self, parser):
        code = '''
roxygenise()
'''
        result = parser.parse(code, "doc.R")
        assert "roxygen2" in result.detected_frameworks

    def test_detect_arrow(self, parser):
        code = '''
library(arrow)
data <- read_parquet("data.parquet")
write_parquet(data, "output.parquet")
'''
        result = parser.parse(code, "io.R")
        assert "arrow" in result.detected_frameworks

    def test_detect_multiple_frameworks(self, parser):
        code = '''
library(shiny)
library(DBI)
library(ggplot2)

server <- function(input, output, session) {
  con <- DBI::dbConnect(RSQLite::SQLite(), "app.db")
  data <- reactiveVal(NULL)

  observeEvent(input$refresh, {
    data(dbGetQuery(con, "SELECT * FROM metrics"))
  })

  output$plot <- renderPlot({
    ggplot(data(), aes(x = date, y = value)) +
      geom_line()
  })
}
'''
        result = parser.parse(code, "app.R")
        assert "shiny" in result.detected_frameworks
        assert "DBI" in result.detected_frameworks
        assert "ggplot2" in result.detected_frameworks


# ===== R VERSION FEATURE DETECTION =====

class TestRVersionFeatures:
    """Tests for R version feature detection."""

    def test_detect_base_pipe(self, parser):
        code = '''
result <- x |> sqrt() |> round(2)
'''
        result = parser.parse(code, "pipe.R")
        assert "base_pipe" in result.detected_r_features

    def test_detect_lambda_syntax(self, parser):
        code = r'''
square <- \(x) x^2
'''
        result = parser.parse(code, "lambda.R")
        assert "lambda" in result.detected_r_features

    def test_no_features_in_old_code(self, parser):
        code = '''
result <- sapply(x, function(val) val + 1)
'''
        result = parser.parse(code, "old.R")
        assert "base_pipe" not in result.detected_r_features
        assert "lambda" not in result.detected_r_features


# ===== DESCRIPTION PARSING =====

class TestDescriptionParsing:
    """Tests for DESCRIPTION file parsing."""

    def test_parse_description(self, parser):
        content = '''Package: mypackage
Title: My Cool Package
Version: 1.2.3
Description: A package that does cool things.
License: MIT + file LICENSE
Depends: R (>= 4.0)
Imports:
    dplyr (>= 1.0),
    ggplot2,
    purrr
Suggests:
    testthat (>= 3.0),
    knitr
Author: Jane Doe
'''
        result = parser.parse_description(content)
        assert result["metadata"]["name"] == "mypackage"
        assert result["metadata"]["version"] == "1.2.3"
        assert "dplyr" in result["dependencies"]
        assert "ggplot2" in result["dependencies"]


# ===== RENV.LOCK PARSING =====

class TestRenvLockParsing:
    """Tests for renv.lock parsing."""

    def test_parse_renv_lock(self, parser):
        content = '''{
  "R": {
    "Version": "4.3.1"
  },
  "Packages": {
    "dplyr": {
      "Package": "dplyr",
      "Version": "1.1.3",
      "Source": "Repository"
    },
    "ggplot2": {
      "Package": "ggplot2",
      "Version": "3.4.4",
      "Source": "Repository"
    }
  }
}'''
        result = parser.parse_renv_lock(content)
        assert "dplyr" in result
        assert result["dplyr"] == "1.1.3"
        assert "ggplot2" in result
        assert result["ggplot2"] == "3.4.4"


# ===== NAMESPACE PARSING =====

class TestNamespaceParsing:
    """Tests for NAMESPACE file parsing."""

    def test_parse_namespace(self, parser):
        content = '''export(my_function)
export(another_function)
exportPattern("^[[:alpha:]]+")
importFrom(dplyr,filter)
importFrom(dplyr,mutate)
import(ggplot2)
'''
        result = parser.parse_namespace(content)
        exports = result["exports"]
        assert len(exports) >= 2
        export_names = [e["name"] for e in exports]
        assert "my_function" in export_names


# ===== COMPREHENSIVE PARSING =====

class TestComprehensiveParsing:
    """Tests for comprehensive R file parsing."""

    def test_complete_r_file(self, parser):
        code = '''
library(R6)
library(dplyr)
library(DBI)

#\' Database Manager
#\'
#\' @description Manages database connections and queries
#\' @export
DatabaseManager <- R6::R6Class("DatabaseManager",
  private = list(
    con = NULL,
    db_name = NULL
  ),
  public = list(
    initialize = function(db_name) {
      private$db_name <- db_name
      private$con <- DBI::dbConnect(RSQLite::SQLite(), db_name)
    },

    query = function(sql, params = list()) {
      DBI::dbGetQuery(private$con, sql, params = params)
    },

    get_users = function(active = TRUE) {
      self$query("SELECT * FROM users WHERE active = ?", list(active)) |>
        as_tibble() |>
        mutate(full_name = paste(first_name, last_name))
    },

    close = function() {
      DBI::dbDisconnect(private$con)
    }
  )
)

#\' Process data pipeline
#\'
#\' @param data Input data frame
#\' @return Processed tibble
process_data <- function(data) {
  data |>
    filter(!is.na(value)) |>
    group_by(category) |>
    summarize(
      mean_val = mean(value, na.rm = TRUE),
      count = n()
    ) |>
    arrange(desc(mean_val))
}

print.summary_result <- function(x, ...) {
  cat(sprintf("Summary: %d categories\\n", nrow(x)))
}
'''
        result = parser.parse(code, "manager.R")

        # Should detect classes
        assert len(result.classes) >= 1
        assert result.classes[0].name == "DatabaseManager"

        # Should detect functions
        func_names = [f.name for f in result.functions]
        assert "process_data" in func_names
        assert "print.summary_result" in func_names

        # Should detect S3 method
        print_fn = next(f for f in result.functions if f.name == "print.summary_result")
        assert print_fn.is_s3_method is True

        # Should detect imports
        assert "R6" in result.imports
        assert "dplyr" in result.imports
        assert "DBI" in result.imports

        # Should detect frameworks
        assert "R6" in result.detected_frameworks
        assert "DBI" in result.detected_frameworks

        # Should detect pipe chains
        assert len(result.pipe_chains) >= 1

        # Should detect R version features (base pipe)
        assert "base_pipe" in result.detected_r_features
