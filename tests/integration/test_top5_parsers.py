"""
Integration tests for the top 5 language parsers.

Each test uses a realistic multi-element code fixture and asserts that the parser
extracts classes, functions, frameworks, and key metadata correctly.

Part of CodeTrellis v5.0 — Phase 3 (Parser Quality)
"""

import pytest
from codetrellis.python_parser_enhanced import EnhancedPythonParser, PythonParseResult
from codetrellis.typescript_parser_enhanced import EnhancedTypeScriptParser, TypeScriptParseResult
from codetrellis.javascript_parser_enhanced import EnhancedJavaScriptParser, JavaScriptParseResult
from codetrellis.java_parser_enhanced import EnhancedJavaParser, JavaParseResult
from codetrellis.csharp_parser_enhanced import EnhancedCSharpParser, CSharpParseResult


# ── Fixtures ─────────────────────────────────────────────

PYTHON_FIXTURE = '''
import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class User:
    """A user in the system."""
    name: str
    email: str
    age: int = 0

    def full_name(self) -> str:
        return self.name

class UserService:
    """Service for user operations."""
    def __init__(self, db):
        self.db = db

    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.find(user_id)

    def list_users(self) -> List[User]:
        return self.db.all()

    async def create_user(self, name: str, email: str) -> User:
        user = User(name=name, email=email)
        await self.db.save(user)
        return user

def validate_email(email: str) -> bool:
    return "@" in email
'''

TYPESCRIPT_FIXTURE = '''
import { Injectable } from '@nestjs/common';
import { Repository } from 'typeorm';

interface UserDTO {
    id: number;
    name: string;
    email: string;
}

type UserRole = 'admin' | 'user' | 'guest';

enum Status {
    Active = 'active',
    Inactive = 'inactive',
}

class UserEntity {
    id: number;
    name: string;
    email: string;
    role: UserRole;
    status: Status;
}

@Injectable()
export class UserService {
    constructor(private readonly repo: Repository<UserEntity>) {}

    async findAll(): Promise<UserDTO[]> {
        return this.repo.find();
    }

    async findById(id: number): Promise<UserDTO | null> {
        return this.repo.findOne({ where: { id } });
    }

    async create(dto: UserDTO): Promise<UserEntity> {
        return this.repo.save(dto);
    }
}

export function isValidEmail(email: string): boolean {
    return email.includes('@');
}
'''

JAVASCRIPT_FIXTURE = '''
const express = require('express');
const router = express.Router();

class AuthMiddleware {
    constructor(secretKey) {
        this.secretKey = secretKey;
    }

    verify(req, res, next) {
        const token = req.headers.authorization;
        if (token) {
            next();
        } else {
            res.status(401).json({ error: 'Unauthorized' });
        }
    }
}

router.get('/api/users', async (req, res) => {
    const users = await UserModel.find();
    res.json(users);
});

router.post('/api/users', async (req, res) => {
    const user = new UserModel(req.body);
    await user.save();
    res.status(201).json(user);
});

router.delete('/api/users/:id', async (req, res) => {
    await UserModel.findByIdAndDelete(req.params.id);
    res.status(204).send();
});

function formatUser(user) {
    return {
        id: user._id,
        name: user.name,
        email: user.email,
    };
}

module.exports = { router, AuthMiddleware, formatUser };
'''

JAVA_FIXTURE = '''
package com.myapp.service;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import javax.persistence.Entity;
import javax.persistence.Id;
import java.util.List;
import java.util.Optional;

@Entity
public class Product {
    @Id
    private Long id;
    private String name;
    private double price;

    public Long getId() { return id; }
    public String getName() { return name; }
    public double getPrice() { return price; }
}

public interface ProductRepository {
    Optional<Product> findById(Long id);
    List<Product> findAll();
    Product save(Product product);
}

@RestController
@RequestMapping("/api/products")
public class ProductController {

    @Autowired
    private ProductRepository repository;

    @GetMapping
    public List<Product> getAll() {
        return repository.findAll();
    }

    @GetMapping("/{id}")
    public Optional<Product> getById(@PathVariable Long id) {
        return repository.findById(id);
    }

    @PostMapping
    public Product create(@RequestBody Product product) {
        return repository.save(product);
    }
}
'''

CSHARP_FIXTURE = '''
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace MyApp.Controllers;

public record ProductDto(int Id, string Name, decimal Price);

public class Product
{
    public int Id { get; set; }
    public string Name { get; set; }
    public decimal Price { get; set; }
}

public class AppDbContext : DbContext
{
    public DbSet<Product> Products { get; set; }
}

[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly AppDbContext _context;

    public ProductsController(AppDbContext context)
    {
        _context = context;
    }

    [HttpGet]
    public async Task<List<Product>> GetAll()
    {
        return await _context.Products.ToListAsync();
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Product>> GetById(int id)
    {
        var product = await _context.Products.FindAsync(id);
        return product ?? (ActionResult<Product>)NotFound();
    }

    [HttpPost]
    public async Task<ActionResult<Product>> Create(ProductDto dto)
    {
        var product = new Product { Name = dto.Name, Price = dto.Price };
        _context.Products.Add(product);
        await _context.SaveChangesAsync();
        return CreatedAtAction(nameof(GetById), new { id = product.Id }, product);
    }
}
'''


# ── Python Parser Tests ──────────────────────────────────

class TestPythonParserIntegration:
    """Integration tests for EnhancedPythonParser (regex-based, no tree-sitter)."""

    def setup_method(self):
        self.parser = EnhancedPythonParser()

    def test_extracts_classes(self):
        result = self.parser.parse(PYTHON_FIXTURE, "user_service.py")
        class_names = {c.name for c in result.classes}
        assert 'User' in class_names
        assert 'UserService' in class_names

    def test_extracts_functions(self):
        result = self.parser.parse(PYTHON_FIXTURE, "user_service.py")
        func_names = {f.name for f in result.functions}
        assert 'validate_email' in func_names

    def test_extracts_dataclasses(self):
        result = self.parser.parse(PYTHON_FIXTURE, "user_service.py")
        dc_names = {d.name for d in result.dataclasses}
        assert 'User' in dc_names

    def test_extracts_imports(self):
        result = self.parser.parse(PYTHON_FIXTURE, "user_service.py")
        assert len(result.imports) >= 2  # os, dataclasses, typing


# ── TypeScript Parser Tests ──────────────────────────────

class TestTypeScriptParserIntegration:
    """Integration tests for EnhancedTypeScriptParser."""

    def setup_method(self):
        self.parser = EnhancedTypeScriptParser()

    def test_extracts_classes(self):
        result = self.parser.parse(TYPESCRIPT_FIXTURE, "user.service.ts")
        class_names = {c.name for c in result.classes}
        assert 'UserEntity' in class_names
        assert 'UserService' in class_names

    def test_extracts_interfaces(self):
        result = self.parser.parse(TYPESCRIPT_FIXTURE, "user.service.ts")
        interface_names = {i.name for i in result.interfaces}
        assert 'UserDTO' in interface_names

    def test_extracts_enums(self):
        result = self.parser.parse(TYPESCRIPT_FIXTURE, "user.service.ts")
        enum_names = {e.name for e in result.enums}
        assert 'Status' in enum_names

    def test_extracts_type_aliases(self):
        result = self.parser.parse(TYPESCRIPT_FIXTURE, "user.service.ts")
        type_names = {t.name for t in result.type_aliases}
        assert 'UserRole' in type_names

    def test_extracts_functions(self):
        result = self.parser.parse(TYPESCRIPT_FIXTURE, "user.service.ts")
        func_names = {f.name for f in result.functions}
        assert 'isValidEmail' in func_names

    def test_detects_frameworks(self):
        result = self.parser.parse(TYPESCRIPT_FIXTURE, "user.service.ts")
        # Should detect NestJS or TypeORM from imports
        assert len(result.detected_frameworks) >= 1


# ── JavaScript Parser Tests ──────────────────────────────

class TestJavaScriptParserIntegration:
    """Integration tests for EnhancedJavaScriptParser."""

    def setup_method(self):
        self.parser = EnhancedJavaScriptParser()

    def test_extracts_classes(self):
        result = self.parser.parse(JAVASCRIPT_FIXTURE, "auth.js")
        class_names = {c.name for c in result.classes}
        assert 'AuthMiddleware' in class_names

    def test_extracts_routes(self):
        result = self.parser.parse(JAVASCRIPT_FIXTURE, "routes.js")
        assert len(result.routes) >= 2  # GET, POST, DELETE

    def test_extracts_functions(self):
        result = self.parser.parse(JAVASCRIPT_FIXTURE, "routes.js")
        func_names = {f.name for f in result.functions}
        assert 'formatUser' in func_names

    def test_detects_express(self):
        result = self.parser.parse(JAVASCRIPT_FIXTURE, "routes.js")
        detected = [f.lower() for f in result.detected_frameworks]
        assert any('express' in f for f in detected)

    def test_extracts_exports(self):
        result = self.parser.parse(JAVASCRIPT_FIXTURE, "routes.js")
        assert len(result.exports) >= 1  # module.exports


# ── Java Parser Tests ────────────────────────────────────

class TestJavaParserIntegration:
    """Integration tests for EnhancedJavaParser."""

    def setup_method(self):
        self.parser = EnhancedJavaParser()

    def test_extracts_classes(self):
        result = self.parser.parse(JAVA_FIXTURE, "ProductController.java")
        class_names = {c.name for c in result.classes}
        assert 'Product' in class_names
        assert 'ProductController' in class_names

    def test_extracts_interfaces(self):
        result = self.parser.parse(JAVA_FIXTURE, "ProductController.java")
        interface_names = {i.name for i in result.interfaces}
        assert 'ProductRepository' in interface_names

    def test_extracts_package(self):
        result = self.parser.parse(JAVA_FIXTURE, "ProductController.java")
        assert result.package_name == 'com.myapp.service'

    def test_extracts_endpoints(self):
        result = self.parser.parse(JAVA_FIXTURE, "ProductController.java")
        assert len(result.endpoints) >= 2  # GET, GET/{id}, POST

    def test_detects_spring(self):
        result = self.parser.parse(JAVA_FIXTURE, "ProductController.java")
        detected = [f.lower() for f in result.detected_frameworks]
        assert any('spring' in f for f in detected)

    def test_extracts_imports(self):
        result = self.parser.parse(JAVA_FIXTURE, "ProductController.java")
        assert len(result.imports) >= 3


# ── C# Parser Tests ──────────────────────────────────────

class TestCSharpParserIntegration:
    """Integration tests for EnhancedCSharpParser."""

    def setup_method(self):
        self.parser = EnhancedCSharpParser()

    def test_extracts_classes(self):
        result = self.parser.parse(CSHARP_FIXTURE, "ProductsController.cs")
        class_names = {c.name for c in result.classes}
        assert 'Product' in class_names
        assert 'ProductsController' in class_names
        assert 'AppDbContext' in class_names

    def test_extracts_records(self):
        result = self.parser.parse(CSHARP_FIXTURE, "ProductsController.cs")
        record_names = {r.name for r in result.records}
        assert 'ProductDto' in record_names

    def test_extracts_namespace(self):
        result = self.parser.parse(CSHARP_FIXTURE, "ProductsController.cs")
        assert result.namespace == 'MyApp.Controllers'

    def test_extracts_endpoints(self):
        result = self.parser.parse(CSHARP_FIXTURE, "ProductsController.cs")
        assert len(result.endpoints) >= 2  # GET, GET/{id}, POST

    def test_detects_aspnet(self):
        result = self.parser.parse(CSHARP_FIXTURE, "ProductsController.cs")
        detected = [f.lower() for f in result.detected_frameworks]
        assert any('aspnet' in f or 'efcore' in f or 'entity' in f for f in detected)

    def test_extracts_usings(self):
        result = self.parser.parse(CSHARP_FIXTURE, "ProductsController.cs")
        assert len(result.usings) >= 3
