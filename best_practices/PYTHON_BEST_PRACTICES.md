# Python Best Practices - Comprehensive Guide

> A comprehensive guide to Python best practices sourced from official documentation and industry standards.

## Table of Contents

- [The Zen of Python](#the-zen-of-python)
- [Code Style (PEP 8)](#code-style-pep-8)
- [Naming Conventions](#naming-conventions)
- [Code Layout](#code-layout)
- [Imports](#imports)
- [Comments and Documentation](#comments-and-documentation)
- [Type Hints](#type-hints)
- [Error Handling](#error-handling)
- [Pythonic Idioms](#pythonic-idioms)
- [Project Structure](#project-structure)
- [Virtual Environments](#virtual-environments)
- [Testing](#testing)
- [Web Frameworks](#web-frameworks)
- [AI/ML Frameworks](#aiml-frameworks)
- [API Development](#api-development)
- [Code Quality Tools](#code-quality-tools)
- [Performance Optimization](#performance-optimization)
- [Security Best Practices](#security-best-practices)

---

## The Zen of Python

_PEP 20 - The guiding principles for Python's design_

```python
>>> import this

Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
```

---

## Code Style (PEP 8)

### Indentation

Use **4 spaces** per indentation level. Never mix tabs and spaces.

```python
# Correct: Aligned with opening delimiter
foo = long_function_name(var_one, var_two,
                         var_three, var_four)

# Correct: Add 4 spaces (extra level) to distinguish arguments
def long_function_name(
        var_one, var_two, var_three,
        var_four):
    print(var_one)

# Correct: Hanging indents should add a level
foo = long_function_name(
    var_one, var_two,
    var_three, var_four)
```

### Maximum Line Length

- **79 characters** for code
- **72 characters** for comments and docstrings

```python
# Use parentheses for line continuation (preferred)
income = (gross_wages
          + taxable_interest
          + (dividends - qualified_dividends)
          - ira_deduction
          - student_loan_interest)

# Backslash continuation (use sparingly)
with open('/path/to/some/file/you/want/to/read') as file_1, \
     open('/path/to/some/file/being/written', 'w') as file_2:
    file_2.write(file_1.read())
```

### Blank Lines

- **2 blank lines** around top-level function and class definitions
- **1 blank line** around method definitions inside a class
- Use blank lines sparingly to indicate logical sections

### String Quotes

Pick a style and stick to it. Use the other quote type to avoid backslashes:

```python
# Consistent single or double quotes
name = 'John'
name = "John"

# Avoid escaping
message = "It's a beautiful day"
message = 'He said "Hello"'

# Triple quotes for docstrings - always use double quotes
"""This is a docstring."""
```

---

## Naming Conventions

| Type              | Convention                    | Example         |
| ----------------- | ----------------------------- | --------------- |
| Package           | lowercase                     | `mypackage`     |
| Module            | lowercase_with_underscores    | `my_module.py`  |
| Class             | CapWords (PascalCase)         | `MyClass`       |
| Exception         | CapWords with "Error" suffix  | `CustomError`   |
| Function          | lowercase_with_underscores    | `my_function()` |
| Variable          | lowercase_with_underscores    | `my_variable`   |
| Constant          | UPPERCASE_WITH_UNDERSCORES    | `MAX_OVERFLOW`  |
| Method            | lowercase_with_underscores    | `get_value()`   |
| Instance Variable | lowercase_with_underscores    | `self.name`     |
| Protected         | \_single_leading_underscore   | `_internal`     |
| Private           | \_\_double_leading_underscore | `__private`     |
| Magic/Dunder      | **double_underscore**         | `__init__`      |
| Type Variable     | CapWords, short               | `T`, `AnyStr`   |

### Names to Avoid

- Never use `l` (lowercase L), `O` (uppercase O), or `I` (uppercase i) as single character names
- Avoid names that shadow built-ins (`list`, `dict`, `str`, `type`, etc.)

```python
# Bad
l = 1
O = 2
list = [1, 2, 3]

# Good
length = 1
offset = 2
items = [1, 2, 3]
```

---

## Code Layout

### Imports

```python
"""This is the module docstring."""

from __future__ import annotations  # Future imports first

__all__ = ['public_function', 'PublicClass']
__version__ = '0.1.0'
__author__ = 'Your Name'

# Standard library imports
import os
import sys
from pathlib import Path
from typing import List, Optional

# Related third-party imports
import numpy as np
import pandas as pd
from flask import Flask, request

# Local application/library specific imports
from mypackage import mymodule
from mypackage.submodule import MyClass
```

### Import Best Practices

```python
# Correct: Imports on separate lines
import os
import sys

# Correct: Multiple imports from one module
from subprocess import Popen, PIPE

# Avoid: Wildcard imports
from module import *  # Don't do this!

# Use absolute imports (preferred)
import mypkg.sibling
from mypkg import sibling
from mypkg.sibling import example

# Explicit relative imports (acceptable for complex layouts)
from . import sibling
from .sibling import example
```

---

## Comments and Documentation

### Block Comments

```python
# This is a block comment that explains the following code.
# Each line starts with a # and a single space.
#
# Paragraphs are separated by a line containing a single #.
```

### Inline Comments

```python
x = x + 1  # Compensate for border (use sparingly)
```

### Docstrings (PEP 257)

```python
def calculate_area(length: float, width: float) -> float:
    """Calculate the area of a rectangle.

    Args:
        length: The length of the rectangle.
        width: The width of the rectangle.

    Returns:
        The area of the rectangle.

    Raises:
        ValueError: If length or width is negative.

    Example:
        >>> calculate_area(5.0, 3.0)
        15.0
    """
    if length < 0 or width < 0:
        raise ValueError("Dimensions must be non-negative")
    return length * width


class Rectangle:
    """A class representing a rectangle.

    Attributes:
        length: The length of the rectangle.
        width: The width of the rectangle.
    """

    def __init__(self, length: float, width: float) -> None:
        """Initialize a Rectangle instance.

        Args:
            length: The length of the rectangle.
            width: The width of the rectangle.
        """
        self.length = length
        self.width = width
```

---

## Type Hints

_PEP 484 - Type Hints for Python_

### Basic Type Hints

```python
from typing import (
    List, Dict, Set, Tuple, Optional, Union,
    Callable, Iterator, Generator, Any,
    TypeVar, Generic
)

# Basic types
name: str = "John"
age: int = 30
price: float = 19.99
is_active: bool = True

# Collections
names: List[str] = ["Alice", "Bob"]
scores: Dict[str, int] = {"Alice": 95, "Bob": 87}
unique_ids: Set[int] = {1, 2, 3}
coordinates: Tuple[float, float] = (10.5, 20.3)

# Optional (can be None)
middle_name: Optional[str] = None

# Union types
identifier: Union[int, str] = 42

# Python 3.10+ syntax
identifier: int | str = 42
middle_name: str | None = None
```

### Function Type Hints

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

def process_items(items: List[int]) -> Dict[str, int]:
    return {"sum": sum(items), "count": len(items)}

# Callable type
def apply_operation(
    values: List[int],
    operation: Callable[[int], int]
) -> List[int]:
    return [operation(v) for v in values]

# Generator
def count_up(limit: int) -> Generator[int, None, None]:
    for i in range(limit):
        yield i
```

### Generic Types

```python
from typing import TypeVar, Generic

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()
```

---

## Error Handling

### Exception Handling Best Practices

```python
# Catch specific exceptions
try:
    value = collection[key]
except KeyError:
    return key_not_found(key)
else:
    return handle_value(value)

# Use context managers for cleanup
with open('file.txt') as f:
    content = f.read()

# Exception chaining
try:
    process_data()
except ValueError as e:
    raise RuntimeError("Processing failed") from e

# Custom exceptions
class ValidationError(Exception):
    """Raised when validation fails."""
    pass

class DatabaseError(Exception):
    """Raised when a database operation fails."""

    def __init__(self, message: str, error_code: int) -> None:
        super().__init__(message)
        self.error_code = error_code
```

### What NOT to Do

```python
# Bad: Bare except clause
try:
    risky_operation()
except:  # Catches everything including SystemExit!
    pass

# Bad: Too broad exception handling
try:
    return handle_value(collection[key])
except KeyError:
    # Will also catch KeyError raised by handle_value()
    return key_not_found(key)

# Bad: Silencing all exceptions
try:
    do_something()
except Exception:
    pass  # Never do this without logging!
```

---

## Pythonic Idioms

### Unpacking

```python
# Tuple unpacking
a, b = b, a  # Swap variables

# Extended unpacking (Python 3)
first, *middle, last = [1, 2, 3, 4, 5]

# Ignoring values
filename = 'document.txt'
basename, _, ext = filename.rpartition('.')

# Enumerate
for index, item in enumerate(items):
    print(f"{index}: {item}")
```

### List Operations

```python
# List comprehension (preferred over map/filter)
squares = [x**2 for x in range(10)]
evens = [x for x in numbers if x % 2 == 0]

# Generator expression (for large datasets)
sum_of_squares = sum(x**2 for x in range(1000000))

# Don't modify list while iterating
# Bad:
for item in items:
    if condition(item):
        items.remove(item)

# Good:
items = [item for item in items if not condition(item)]
```

### Dictionary Operations

```python
# Use .get() with default
value = d.get('key', 'default_value')

# Check membership
if 'key' in d:
    process(d['key'])

# Dictionary comprehension
squared = {k: v**2 for k, v in pairs.items()}

# Merge dictionaries (Python 3.9+)
merged = dict1 | dict2

# Update in place
dict1 |= dict2
```

### String Operations

```python
# Join strings efficiently
words = ['Hello', 'World']
sentence = ' '.join(words)

# Use f-strings (Python 3.6+)
name = "Alice"
greeting = f"Hello, {name}!"

# String methods for checks
if text.startswith('Hello'):  # Not text[:5] == 'Hello'
    pass

if text.endswith('.py'):  # Not text[-3:] == '.py'
    pass
```

### Truth Value Testing

```python
# Check truthiness directly
if items:  # Not: if len(items) > 0
    process(items)

if not items:  # Not: if len(items) == 0
    return

# Explicit None checks
if value is None:  # Not: if value == None
    pass

if value is not None:  # Not: if not value is None
    pass
```

### Context Managers

```python
# File handling
with open('file.txt', 'r') as f:
    content = f.read()

# Multiple context managers
with open('input.txt') as fin, open('output.txt', 'w') as fout:
    fout.write(fin.read())

# Custom context manager
from contextlib import contextmanager

@contextmanager
def managed_resource():
    resource = acquire_resource()
    try:
        yield resource
    finally:
        release_resource(resource)
```

---

## Project Structure

### Recommended Layout

```
myproject/
├── README.md
├── LICENSE
├── pyproject.toml          # Modern Python packaging (PEP 518)
├── setup.py                # Legacy packaging (optional)
├── setup.cfg               # Setup configuration
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── .gitignore
├── .env.example
├── Makefile               # Common commands
├── docs/
│   ├── conf.py
│   └── index.rst
├── src/
│   └── myproject/
│       ├── __init__.py
│       ├── __main__.py    # For `python -m myproject`
│       ├── core/
│       │   ├── __init__.py
│       │   └── models.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py
│       └── utils/
│           ├── __init__.py
│           └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_core/
│   │   └── test_models.py
│   └── test_api/
│       └── test_routes.py
└── scripts/
    └── setup_dev.sh
```

### pyproject.toml (Modern Approach)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "myproject"
version = "0.1.0"
description = "A brief description"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
dependencies = [
    "requests>=2.28.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[project.scripts]
myproject = "myproject.__main__:main"

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.9"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=src/myproject"
```

---

## Virtual Environments

### Creating and Managing Virtual Environments

```bash
# Using venv (built-in)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Using uv (modern, fast)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Using conda
conda create -n myenv python=3.11
conda activate myenv

# Deactivate
deactivate
```

### Requirements Files

```text
# requirements.txt
requests>=2.28.0,<3.0.0
pydantic>=2.0.0
sqlalchemy>=2.0.0

# requirements-dev.txt
-r requirements.txt
pytest>=7.0.0
black>=23.0.0
mypy>=1.0.0
```

---

## Testing

### pytest Best Practices

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"name": "Test", "value": 42}

@pytest.fixture
def db_connection():
    """Provide a database connection."""
    conn = create_connection()
    yield conn
    conn.close()

# tests/test_example.py
import pytest

class TestCalculator:
    """Tests for the Calculator class."""

    def test_add_positive_numbers(self):
        """Test adding two positive numbers."""
        assert add(2, 3) == 5

    def test_add_negative_numbers(self):
        """Test adding two negative numbers."""
        assert add(-2, -3) == -5

    @pytest.mark.parametrize("a,b,expected", [
        (1, 2, 3),
        (0, 0, 0),
        (-1, 1, 0),
    ])
    def test_add_various_inputs(self, a, b, expected):
        """Test addition with various inputs."""
        assert add(a, b) == expected

    def test_division_by_zero_raises(self):
        """Test that division by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(10, 0)
```

### Test Organization

```
tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests
│   ├── test_models.py
│   └── test_utils.py
├── integration/          # Integration tests
│   └── test_api.py
└── e2e/                  # End-to-end tests
    └── test_workflows.py
```

---

## Web Frameworks

### Django - Full-Featured Framework

**Best for:** Large applications, admin interfaces, rapid development

```python
# Django project structure
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── myapp/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    └── urls.py

# models.py
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# views.py
from django.shortcuts import render, get_object_or_404
from .models import Article

def article_list(request):
    articles = Article.objects.all()
    return render(request, 'articles/list.html', {'articles': articles})
```

### Flask - Lightweight Microframework

**Best for:** Small to medium applications, APIs, microservices

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/api/users', methods=['GET', 'POST'])
def users():
    if request.method == 'POST':
        data = request.get_json()
        # Process data
        return jsonify({'status': 'created'}), 201
    return jsonify({'users': []})

# Application factory pattern
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
```

### FastAPI - Modern Async Framework

**Best for:** High-performance APIs, automatic documentation, type safety

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="My API",
    description="A sample API",
    version="1.0.0"
)

# Pydantic models for request/response
class Item(BaseModel):
    name: str
    price: float
    is_offer: Optional[bool] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

# Dependency injection
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int, q: Optional[str] = None):
    return {"id": item_id, "name": "Item", "price": 9.99}

@app.post("/items/", response_model=ItemResponse, status_code=201)
async def create_item(item: Item, db: Session = Depends(get_db)):
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    return db_item
```

---

## AI/ML Frameworks

### PyTorch - Deep Learning

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# Define a neural network
class SimpleNet(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

# Training loop
def train(model, dataloader, criterion, optimizer, device):
    model.train()
    for batch_idx, (data, target) in enumerate(dataloader):
        data, target = data.to(device), target.to(device)

        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

# Best practices
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SimpleNet(784, 256, 10).to(device)
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()
```

### TensorFlow/Keras - Deep Learning

```python
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Sequential model
model = keras.Sequential([
    layers.Dense(64, activation='relu', input_shape=(784,)),
    layers.Dropout(0.2),
    layers.Dense(64, activation='relu'),
    layers.Dense(10, activation='softmax')
])

# Compile and train
model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

model.fit(x_train, y_train, epochs=10, validation_split=0.2)

# Custom training loop
@tf.function
def train_step(model, x, y, loss_fn, optimizer):
    with tf.GradientTape() as tape:
        predictions = model(x, training=True)
        loss = loss_fn(y, predictions)
    gradients = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    return loss
```

### scikit-learn - Machine Learning

```python
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# Data preparation
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Pipeline for preprocessing and modeling
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

# Cross-validation
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5)
print(f"CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

# Fit and evaluate
pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
print(classification_report(y_test, y_pred))
```

### Hugging Face Transformers - NLP

```python
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)
from datasets import load_dataset

# Load pre-trained model and tokenizer
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=2
)

# Tokenize dataset
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=512
    )

dataset = load_dataset("imdb")
tokenized_dataset = dataset.map(tokenize_function, batched=True)

# Training
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir="./logs",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
)

trainer.train()
```

---

## API Development

### RESTful API Design

```python
# FastAPI example with full CRUD
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4

app = FastAPI()

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')

class User(UserBase):
    id: UUID

    class Config:
        from_attributes = True

# CRUD endpoints
@app.get("/users", response_model=List[User])
async def list_users(skip: int = 0, limit: int = 100):
    """List all users with pagination."""
    return users[skip:skip + limit]

@app.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Create a new user."""
    new_user = User(id=uuid4(), **user.dict(exclude={'password'}))
    return new_user

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: UUID):
    """Get a specific user by ID."""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return users_db[user_id]

@app.patch("/users/{user_id}", response_model=User)
async def update_user(user_id: UUID, user_update: UserUpdate):
    """Partially update a user."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    stored_user = users_db[user_id]
    update_data = user_update.dict(exclude_unset=True)
    updated_user = stored_user.copy(update=update_data)
    users_db[user_id] = updated_user
    return updated_user

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID):
    """Delete a user."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    del users_db[user_id]
```

### GraphQL API (Strawberry)

```python
import strawberry
from typing import List

@strawberry.type
class User:
    id: int
    name: str
    email: str

@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> List[User]:
        return get_all_users()

    @strawberry.field
    def user(self, id: int) -> User:
        return get_user_by_id(id)

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, name: str, email: str) -> User:
        return create_new_user(name, email)

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

---

## Code Quality Tools

### Linting and Formatting

```bash
# Black - Code formatter
pip install black
black .

# Ruff - Fast linter (replaces flake8, isort, etc.)
pip install ruff
ruff check .
ruff check --fix .

# mypy - Static type checker
pip install mypy
mypy src/

# isort - Import sorter
pip install isort
isort .
```

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## Performance Optimization

### Profiling

```python
import cProfile
import pstats
from pstats import SortKey

# Profile a function
cProfile.run('my_function()', 'output.prof')

# Analyze results
p = pstats.Stats('output.prof')
p.sort_stats(SortKey.CUMULATIVE).print_stats(10)

# Using line_profiler for line-by-line analysis
# pip install line_profiler
# kernprof -l -v script.py
```

### Memory Optimization

```python
# Use generators for large datasets
def read_large_file(file_path):
    with open(file_path) as f:
        for line in f:
            yield line.strip()

# Use __slots__ for memory efficiency
class Point:
    __slots__ = ['x', 'y']

    def __init__(self, x, y):
        self.x = x
        self.y = y

# Use itertools for memory-efficient operations
from itertools import islice, chain

# Process in chunks
def chunks(iterable, size):
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk
```

### Async Programming

```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# Run async code
results = asyncio.run(fetch_all(urls))
```

---

## Security Best Practices

### Input Validation

```python
from pydantic import BaseModel, validator, EmailStr
import re

class UserInput(BaseModel):
    username: str
    email: EmailStr
    password: str

    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain a digit')
        return v
```

### Environment Variables

```python
import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

@lru_cache
def get_settings():
    return Settings()

# Usage
settings = get_settings()
database_url = settings.database_url
```

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### JWT Authentication

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("Invalid token")
```

---

## References

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 20 - The Zen of Python](https://peps.python.org/pep-0020/)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [Python Official Documentation](https://docs.python.org/3/)
- [The Hitchhiker's Guide to Python](https://docs.python-guide.org/)
- [Real Python Best Practices](https://realpython.com/tutorials/best-practices/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PyTorch Documentation](https://pytorch.org/docs/stable/)
- [TensorFlow Guide](https://www.tensorflow.org/guide)
- [scikit-learn Documentation](https://scikit-learn.org/stable/)

---

_Last Updated: February 2026_
