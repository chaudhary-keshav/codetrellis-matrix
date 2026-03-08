"""
Tests for RFunctionExtractor — functions, S3 methods, operators,
lambda syntax, pipe chains, roxygen docs.

Part of CodeTrellis v4.26 R Language Support.
"""

import pytest
from codetrellis.extractors.r.function_extractor import RFunctionExtractor


@pytest.fixture
def extractor():
    return RFunctionExtractor()


# ===== BASIC FUNCTION EXTRACTION =====

class TestBasicFunctionExtraction:
    """Tests for basic R function extraction."""

    def test_simple_function(self, extractor):
        code = '''
add <- function(x, y) {
  x + y
}
'''
        result = extractor.extract(code, "math.R")
        functions = result["functions"]
        assert len(functions) >= 1
        fn = functions[0]
        assert fn.name == "add"
        assert len(fn.parameters) == 2
        assert fn.parameters[0].name == "x"
        assert fn.parameters[1].name == "y"

    def test_function_with_defaults(self, extractor):
        code = '''
greet <- function(name, greeting = "Hello") {
  paste(greeting, name)
}
'''
        result = extractor.extract(code, "greet.R")
        functions = result["functions"]
        assert len(functions) >= 1
        fn = functions[0]
        assert fn.name == "greet"
        params = fn.parameters
        assert len(params) == 2
        assert params[1].name == "greeting"
        assert params[1].default_value == '"Hello"'

    def test_function_with_dots(self, extractor):
        code = '''
my_plot <- function(data, ...) {
  plot(data, ...)
}
'''
        result = extractor.extract(code, "plot.R")
        functions = result["functions"]
        assert len(functions) >= 1
        fn = functions[0]
        assert any(p.name == "..." for p in fn.parameters)

    def test_multiple_functions(self, extractor):
        code = '''
first <- function(x) x[1]
last <- function(x) x[length(x)]
middle <- function(x) x[ceiling(length(x) / 2)]
'''
        result = extractor.extract(code, "utils.R")
        functions = result["functions"]
        assert len(functions) >= 3
        names = [f.name for f in functions]
        assert "first" in names
        assert "last" in names
        assert "middle" in names


# ===== S3 METHOD DETECTION =====

class TestS3MethodDetection:
    """Tests for S3 method detection."""

    def test_s3_method(self, extractor):
        code = '''
print.currency <- function(x, ...) {
  cat(sprintf("%s %.2f\\n", x$code, x$amount))
}
'''
        result = extractor.extract(code, "currency.R")
        functions = result["functions"]
        assert len(functions) >= 1
        fn = functions[0]
        assert fn.name == "print.currency"
        assert fn.is_s3_method is True
        assert fn.s3_generic == "print"
        assert fn.s3_class == "currency"

    def test_s3_summary_method(self, extractor):
        code = '''
summary.model_result <- function(object, ...) {
  cat("Model Result Summary\\n")
}
'''
        result = extractor.extract(code, "model.R")
        functions = result["functions"]
        assert len(functions) >= 1
        fn = functions[0]
        assert fn.is_s3_method is True
        assert fn.s3_generic == "summary"


# ===== OPERATOR EXTRACTION =====

class TestOperatorExtraction:
    """Tests for operator extraction."""

    def test_infix_operator(self, extractor):
        code = '''
`%+%` <- function(a, b) {
  paste0(a, b)
}
'''
        result = extractor.extract(code, "operators.R")
        functions = result["functions"]
        assert len(functions) >= 1
        fn = functions[0]
        assert fn.is_operator is True


# ===== LAMBDA SYNTAX (R 4.1+) =====

class TestLambdaSyntax:
    """Tests for R 4.1+ lambda syntax."""

    def test_lambda_in_assignment(self, extractor):
        code = 'square <- \\(x) x^2\n'
        result = extractor.extract(code, "lambda.R")
        functions = result["functions"]
        assert len(functions) >= 1
        fn = functions[0]
        assert fn.name == "square"


# ===== ROXYGEN DOCUMENTATION =====

class TestRoxygenDocs:
    """Tests for roxygen2 documentation extraction."""

    def test_roxygen_doc(self, extractor):
        code = '''
#\' Calculate BMI
#\'
#\' @param weight Weight in kilograms
#\' @param height Height in meters
#\' @return Numeric BMI value
#\' @export
calculate_bmi <- function(weight, height) {
  weight / height^2
}
'''
        result = extractor.extract(code, "bmi.R")
        functions = result["functions"]
        assert len(functions) >= 1
        fn = functions[0]
        assert fn.name == "calculate_bmi"
        assert fn.doc_comment is not None
        assert "BMI" in fn.doc_comment or "weight" in fn.doc_comment


# ===== PIPE CHAIN EXTRACTION =====

class TestPipeChainExtraction:
    """Tests for pipe chain extraction."""

    def test_base_pipe_chain(self, extractor):
        code = '''
result <- mtcars |>
  subset(cyl == 4) |>
  transform(kpl = mpg * 0.425) |>
  head()
'''
        result = extractor.extract(code, "pipes.R")
        chains = result["pipe_chains"]
        assert len(chains) >= 1
        chain = chains[0]
        assert chain.pipe_type == "|>"
        assert chain.length >= 3

    def test_magrittr_pipe_chain(self, extractor):
        code = '''
result <- data %>%
  filter(status == "active") %>%
  mutate(score = x * 2) %>%
  summarize(total = sum(score))
'''
        result = extractor.extract(code, "pipes.R")
        chains = result["pipe_chains"]
        assert len(chains) >= 1
        chain = chains[0]
        assert chain.pipe_type == "%>%"

    def test_no_pipe_chains(self, extractor):
        code = '''
x <- 1 + 2
y <- sqrt(x)
'''
        result = extractor.extract(code, "simple.R")
        chains = result["pipe_chains"]
        assert len(chains) == 0
