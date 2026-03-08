"""
Tests for RTypeExtractor — R6 classes, R5 Reference classes, S4 classes, S3 constructors,
S7/R7 classes, generics, S4 methods, environments.

Part of CodeTrellis v4.26 R Language Support.
"""

import pytest
from codetrellis.extractors.r.type_extractor import RTypeExtractor


@pytest.fixture
def extractor():
    return RTypeExtractor()


# ===== R6 CLASS EXTRACTION =====

class TestR6ClassExtraction:
    """Tests for R6 class extraction."""

    def test_simple_r6_class(self, extractor):
        code = '''
Person <- R6::R6Class("Person",
  public = list(
    name = NULL,
    initialize = function(name) {
      self$name <- name
    },
    greet = function() {
      cat(paste0("Hello, ", self$name, "\\n"))
    }
  )
)
'''
        result = extractor.extract(code, "person.R")
        classes = result["classes"]
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "Person"
        assert cls.kind == "R6"

    def test_r6_class_with_private(self, extractor):
        code = '''
Counter <- R6::R6Class("Counter",
  private = list(
    count = 0
  ),
  public = list(
    increment = function() {
      private$count <- private$count + 1
    },
    get_count = function() {
      private$count
    }
  )
)
'''
        result = extractor.extract(code, "counter.R")
        classes = result["classes"]
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "Counter"
        assert cls.kind == "R6"

    def test_r6_class_with_inheritance(self, extractor):
        code = '''
Employee <- R6::R6Class("Employee",
  inherit = Person,
  public = list(
    title = NULL,
    initialize = function(name, title) {
      super$initialize(name)
      self$title <- title
    }
  )
)
'''
        result = extractor.extract(code, "employee.R")
        classes = result["classes"]
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "Employee"
        assert cls.parent_class == "Person"

    def test_r6_class_with_active_bindings(self, extractor):
        code = '''
DBPool <- R6::R6Class("DBPool",
  active = list(
    size = function() length(private$connections),
    available = function() sum(vapply(private$connections, is_free, logical(1)))
  ),
  private = list(
    connections = NULL
  ),
  public = list(
    initialize = function() {
      private$connections <- list()
    }
  )
)
'''
        result = extractor.extract(code, "pool.R")
        classes = result["classes"]
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "DBPool"


# ===== S4 CLASS EXTRACTION =====

class TestS4ClassExtraction:
    """Tests for S4 class extraction."""

    def test_s4_class(self, extractor):
        code = '''
setClass("TimeSeries",
  representation(
    values = "numeric",
    timestamps = "POSIXct",
    frequency = "character"
  )
)
'''
        result = extractor.extract(code, "timeseries.R")
        classes = result["classes"]
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "TimeSeries"
        assert cls.kind == "S4"

    def test_s4_class_with_contains(self, extractor):
        code = '''
setClass("IndexedTimeSeries",
  contains = "TimeSeries",
  representation(
    index = "character"
  )
)
'''
        result = extractor.extract(code, "indexed_ts.R")
        classes = result["classes"]
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "IndexedTimeSeries"
        assert cls.parent_class == "TimeSeries"

    def test_s4_generic(self, extractor):
        code = '''
setGeneric("resample", function(x, freq, ...) standardGeneric("resample"))
'''
        result = extractor.extract(code, "generics.R")
        generics = result["generics"]
        assert len(generics) >= 1
        gen = generics[0]
        assert gen.name == "resample"

    def test_s4_method(self, extractor):
        code = '''
setMethod("resample", "TimeSeries", function(x, freq, ...) {
  # implementation
})
'''
        result = extractor.extract(code, "methods.R")
        s4_methods = result["s4_methods"]
        assert len(s4_methods) >= 1
        method = s4_methods[0]
        assert method.generic_name == "resample"


# ===== S3 CLASS EXTRACTION =====

class TestS3ClassExtraction:
    """Tests for S3 class extraction."""

    def test_s3_constructor_with_structure(self, extractor):
        code = '''
new_currency <- function(amount, code = "USD") {
  structure(
    list(amount = amount, code = code),
    class = "currency"
  )
}
'''
        result = extractor.extract(code, "currency.R")
        classes = result["classes"]
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "currency"
        assert cls.kind == "S3"

    def test_s3_class_assignment(self, extractor):
        code = '''
new_point <- function(x, y) {
  obj <- list(x = x, y = y)
  class(obj) <- "point"
  obj
}
'''
        result = extractor.extract(code, "point.R")
        classes = result["classes"]
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "point"
        assert cls.kind == "S3"


# ===== R5 REFERENCE CLASS EXTRACTION =====

class TestR5ClassExtraction:
    """Tests for R5 Reference class extraction."""

    def test_reference_class(self, extractor):
        code = '''
Counter <- setRefClass("Counter",
  fields = list(
    count = "integer"
  ),
  methods = list(
    increment = function() {
      count <<- count + 1L
    }
  )
)
'''
        result = extractor.extract(code, "counter.R")
        classes = result["classes"]
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "Counter"
        assert cls.kind == "R5"


# ===== S7/R7 CLASS EXTRACTION =====

class TestS7ClassExtraction:
    """Tests for S7/R7 class extraction."""

    def test_s7_class(self, extractor):
        code = '''
Dog <- new_class("Dog",
  properties = list(
    name = class_character,
    age = class_double
  )
)
'''
        result = extractor.extract(code, "dog.R")
        classes = result["classes"]
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "Dog"
        assert cls.kind == "S7"

    def test_s7_generic(self, extractor):
        code = '''
speak <- new_generic("speak", "x")
'''
        result = extractor.extract(code, "generics.R")
        generics = result["generics"]
        assert len(generics) >= 1
        gen = generics[0]
        assert gen.name == "speak"
        assert gen.kind == "S7"


# ===== ENVIRONMENT EXTRACTION =====

class TestEnvironmentExtraction:
    """Tests for R environment extraction."""

    def test_new_env(self, extractor):
        code = '''
cache <- new.env(parent = emptyenv())
'''
        result = extractor.extract(code, "cache.R")
        envs = result["environments"]
        assert len(envs) >= 1
        env = envs[0]
        assert env.name == "cache"
