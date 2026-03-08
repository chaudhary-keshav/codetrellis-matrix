"""
Tests for JavaScriptAttributeExtractor — import, export, JSDoc, decorator, dynamic import extraction.

Part of CodeTrellis v4.30 JavaScript Language Support.
"""

import pytest
from codetrellis.extractors.javascript.attribute_extractor import (
    JavaScriptAttributeExtractor,
    JSImportInfo,
    JSExportInfo,
    JSJSDocInfo,
    JSDecoratorInfo,
    JSDynamicImportInfo,
)


@pytest.fixture
def extractor():
    return JavaScriptAttributeExtractor()


class TestESMImports:
    """Tests for ES6 module import extraction."""

    def test_default_import(self, extractor):
        code = '''
import React from 'react';
import express from 'express';
'''
        result = extractor.extract(code, "app.js")
        imports = result.get('imports', [])
        assert len(imports) >= 2
        react_imports = [i for i in imports if i.source == 'react']
        assert len(react_imports) >= 1
        assert react_imports[0].default_import == "React"
        assert react_imports[0].import_type == "es6"

    def test_named_imports(self, extractor):
        code = '''
import { useState, useEffect, useCallback } from 'react';
import { Router, Route, Link } from 'react-router-dom';
'''
        result = extractor.extract(code, "component.jsx")
        imports = result.get('imports', [])
        assert len(imports) >= 2
        react_imports = [i for i in imports if i.source == 'react']
        assert len(react_imports) >= 1
        assert 'useState' in react_imports[0].named_imports

    def test_namespace_import(self, extractor):
        code = '''
import * as path from 'path';
import * as fs from 'fs';
'''
        result = extractor.extract(code, "utils.mjs")
        imports = result.get('imports', [])
        assert len(imports) >= 2
        path_imports = [i for i in imports if i.source == 'path']
        assert len(path_imports) >= 1
        assert path_imports[0].namespace_import == "path"

    def test_mixed_import(self, extractor):
        code = '''
import React, { useState, useEffect } from 'react';
'''
        result = extractor.extract(code, "app.jsx")
        imports = result.get('imports', [])
        assert len(imports) >= 1

    def test_side_effect_import(self, extractor):
        code = '''
import './styles.css';
import 'dotenv/config';
'''
        result = extractor.extract(code, "entry.js")
        imports = result.get('imports', [])
        assert len(imports) >= 1


class TestCommonJSImports:
    """Tests for CommonJS require extraction."""

    def test_require(self, extractor):
        code = '''
const express = require('express');
const path = require('path');
const { readFile, writeFile } = require('fs/promises');
'''
        result = extractor.extract(code, "server.cjs")
        imports = result.get('imports', [])
        assert len(imports) >= 2
        express_imports = [i for i in imports if i.source == 'express']
        assert len(express_imports) >= 1
        assert express_imports[0].import_type == "commonjs"

    def test_destructured_require(self, extractor):
        code = '''
const { Schema, model } = require('mongoose');
'''
        result = extractor.extract(code, "model.js")
        imports = result.get('imports', [])
        assert len(imports) >= 1


class TestExports:
    """Tests for export extraction."""

    def test_named_exports(self, extractor):
        code = '''
export const PI = 3.14159;
export function add(a, b) { return a + b; }
export class Calculator {}
'''
        result = extractor.extract(code, "math.js")
        exports = result.get('exports', [])
        assert len(exports) >= 1

    def test_default_export(self, extractor):
        code = '''
export default function main() {
    console.log('Hello');
}
'''
        result = extractor.extract(code, "main.js")
        exports = result.get('exports', [])
        assert len(exports) >= 1
        default_exports = [e for e in exports if e.export_type == 'default']
        assert len(default_exports) >= 1

    def test_reexport(self, extractor):
        code = '''
export { default as Button } from './Button';
export { Input, Select } from './FormElements';
export * from './utils';
'''
        result = extractor.extract(code, "index.js")
        exports = result.get('exports', [])
        assert len(exports) >= 1

    def test_commonjs_exports(self, extractor):
        code = '''
module.exports = {
    createUser,
    deleteUser,
    updateUser,
};
'''
        result = extractor.extract(code, "users.cjs")
        exports = result.get('exports', [])
        assert len(exports) >= 1

    def test_module_exports_single(self, extractor):
        code = '''
module.exports = Router;
'''
        result = extractor.extract(code, "router.js")
        exports = result.get('exports', [])
        assert len(exports) >= 1


class TestJSDoc:
    """Tests for JSDoc comment extraction."""

    def test_function_jsdoc(self, extractor):
        code = '''
/**
 * Calculate the total price including tax.
 * @param {number} price - The base price.
 * @param {number} taxRate - The tax rate as a decimal.
 * @returns {number} The total price with tax.
 */
function calculateTotal(price, taxRate) {
    return price * (1 + taxRate);
}
'''
        result = extractor.extract(code, "calc.js")
        jsdoc = result.get('jsdoc', [])
        assert len(jsdoc) >= 1
        doc = jsdoc[0]
        assert 'total price' in doc.description.lower() or 'calculate' in doc.description.lower()

    def test_typedef_jsdoc(self, extractor):
        code = '''
/**
 * @typedef {Object} UserConfig
 * @property {string} name - User's name
 * @property {number} age - User's age
 * @property {string} [email] - Optional email
 */
'''
        result = extractor.extract(code, "types.js")
        jsdoc = result.get('jsdoc', [])
        assert len(jsdoc) >= 1

    def test_class_jsdoc(self, extractor):
        code = '''
/**
 * Represents a database connection pool.
 * @class
 * @param {Object} config - Pool configuration
 */
class ConnectionPool {
    constructor(config) {
        this.config = config;
    }
}
'''
        result = extractor.extract(code, "pool.js")
        jsdoc = result.get('jsdoc', [])
        assert len(jsdoc) >= 1


class TestDecorators:
    """Tests for decorator extraction (Stage 3 / Babel)."""

    def test_class_decorator(self, extractor):
        code = '''
@injectable()
@singleton
class UserService {
    constructor() {}
}
'''
        result = extractor.extract(code, "service.js")
        decorators = result.get('decorators', [])
        assert len(decorators) >= 1

    def test_method_decorator(self, extractor):
        code = '''
class Controller {
    @validate
    @log
    handleRequest(req) {}
}
'''
        result = extractor.extract(code, "controller.js")
        decorators = result.get('decorators', [])
        assert len(decorators) >= 1


class TestDynamicImports:
    """Tests for dynamic import extraction."""

    def test_dynamic_import(self, extractor):
        code = '''
const module = await import('./heavy-module.js');
'''
        result = extractor.extract(code, "lazy.js")
        dynamic_imports = result.get('dynamic_imports', [])
        assert len(dynamic_imports) >= 1
        assert dynamic_imports[0].source == "./heavy-module.js"

    def test_react_lazy(self, extractor):
        code = '''
const Dashboard = React.lazy(() => import('./Dashboard'));
const Settings = React.lazy(() => import('./Settings'));
'''
        result = extractor.extract(code, "app.jsx")
        dynamic_imports = result.get('dynamic_imports', [])
        assert len(dynamic_imports) >= 1
        lazy_imports = [di for di in dynamic_imports if di.is_lazy]
        assert len(lazy_imports) >= 1

    def test_conditional_import(self, extractor):
        code = '''
if (process.env.NODE_ENV === 'development') {
    const devTools = await import('./dev-tools');
}
'''
        result = extractor.extract(code, "conditional.js")
        dynamic_imports = result.get('dynamic_imports', [])
        assert len(dynamic_imports) >= 1
