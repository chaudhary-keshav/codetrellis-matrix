"""
Tests for TypeScriptAttributeExtractor — imports, exports, decorators, namespaces, TSDoc.

Part of CodeTrellis v4.31 TypeScript Language Support.
"""

import pytest
from codetrellis.extractors.typescript.attribute_extractor import (
    TypeScriptAttributeExtractor,
    TSImportInfo,
    TSExportInfo,
    TSDecoratorInfo,
    TSNamespaceInfo,
    TSTripleSlashDirective,
    TSTSDocInfo,
)


@pytest.fixture
def extractor():
    return TypeScriptAttributeExtractor()


class TestImportExtraction:
    """Tests for import extraction."""

    def test_named_imports(self, extractor):
        code = '''
import { Component, OnInit, Input } from '@angular/core';
'''
        result = extractor.extract(code, "component.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 1
        imp = imports[0]
        assert imp.source == "@angular/core"
        assert len(imp.named_imports) >= 2

    def test_default_import(self, extractor):
        code = '''
import React from 'react';
'''
        result = extractor.extract(code, "app.tsx")
        imports = result.get('imports', [])
        assert len(imports) >= 1
        imp = imports[0]
        assert imp.default_import == "React"

    def test_namespace_import(self, extractor):
        code = '''
import * as path from 'path';
'''
        result = extractor.extract(code, "utils.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 1
        imp = imports[0]
        assert imp.namespace_import == "path"

    def test_type_only_import(self, extractor):
        code = '''
import type { User, Role } from './types';
'''
        result = extractor.extract(code, "service.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 1
        imp = imports[0]
        assert imp.is_type_only is True

    def test_side_effect_import(self, extractor):
        code = '''
import 'reflect-metadata';
'''
        result = extractor.extract(code, "main.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 1
        imp = imports[0]
        assert imp.source == "reflect-metadata"

    def test_combined_import(self, extractor):
        code = '''
import React, { useState, useEffect } from 'react';
'''
        result = extractor.extract(code, "app.tsx")
        imports = result.get('imports', [])
        assert len(imports) >= 1


class TestExportExtraction:
    """Tests for export extraction."""

    def test_named_exports(self, extractor):
        code = '''
export class UserService {}
export interface Config {}
export type Status = 'ok' | 'error';
export function helper(): void {}
export const VERSION = '1.0';
'''
        result = extractor.extract(code, "index.ts")
        exports = result.get('exports', [])
        assert len(exports) >= 4

    def test_default_export(self, extractor):
        code = '''
export default class App {
    start(): void {}
}
'''
        result = extractor.extract(code, "app.ts")
        exports = result.get('exports', [])
        default_exports = [e for e in exports if e.export_type == "default"]
        assert len(default_exports) >= 1

    def test_type_only_export(self, extractor):
        code = '''
export type { User, Role } from './types';
'''
        result = extractor.extract(code, "index.ts")
        exports = result.get('exports', [])
        type_exports = [e for e in exports if e.is_type_only]
        assert len(type_exports) >= 1

    def test_re_export(self, extractor):
        code = '''
export { UserService } from './user.service';
export { default as Config } from './config';
export * from './utils';
'''
        result = extractor.extract(code, "index.ts")
        exports = result.get('exports', [])
        re_exports = [e for e in exports if e.source]
        assert len(re_exports) >= 2

    def test_namespace_export(self, extractor):
        code = '''
export * as validators from './validators';
'''
        result = extractor.extract(code, "index.ts")
        exports = result.get('exports', [])
        assert len(exports) >= 1


class TestDecoratorExtraction:
    """Tests for decorator extraction."""

    def test_class_decorators(self, extractor):
        code = '''
@Injectable()
@Controller('users')
export class UsersController {
    @Get()
    findAll(): User[] {
        return [];
    }
}
'''
        result = extractor.extract(code, "users.controller.ts")
        decorators = result.get('decorators', [])
        assert len(decorators) >= 2

    def test_method_decorators(self, extractor):
        code = '''
export class AppModule {
    @UseGuards(AuthGuard)
    @Post('login')
    login(@Body() dto: LoginDto): Promise<Token> {
        return this.authService.login(dto);
    }
}
'''
        result = extractor.extract(code, "app.module.ts")
        decorators = result.get('decorators', [])
        assert len(decorators) >= 1


class TestNamespaceExtraction:
    """Tests for namespace/module extraction."""

    def test_namespace(self, extractor):
        code = '''
export namespace Validators {
    export function isEmail(value: string): boolean {
        return /^[^@]+@[^@]+$/.test(value);
    }

    export function isRequired(value: string): boolean {
        return value.length > 0;
    }
}
'''
        result = extractor.extract(code, "validators.ts")
        namespaces = result.get('namespaces', [])
        assert len(namespaces) >= 1
        ns = namespaces[0]
        assert ns.name == "Validators"

    def test_module_augmentation(self, extractor):
        code = '''
declare module 'express' {
    interface Request {
        user?: User;
        token?: string;
    }
}
'''
        result = extractor.extract(code, "types.d.ts")
        namespaces = result.get('namespaces', [])
        assert len(namespaces) >= 1
        ns = namespaces[0]
        assert ns.is_module_augmentation is True


class TestTripleSlashDirectives:
    """Tests for triple-slash directive extraction."""

    def test_reference_directives(self, extractor):
        code = '''
/// <reference types="node" />
/// <reference path="./global.d.ts" />

export function readFile(path: string): string {
    return '';
}
'''
        result = extractor.extract(code, "index.ts")
        directives = result.get('triple_slash_directives', [])
        assert len(directives) >= 1


class TestTSDocExtraction:
    """Tests for TSDoc comment extraction."""

    def test_tsdoc_function(self, extractor):
        code = '''
/**
 * Calculates the sum of two numbers.
 *
 * @param a - The first number
 * @param b - The second number
 * @returns The sum of a and b
 *
 * @example
 * ```ts
 * const result = add(1, 2); // 3
 * ```
 *
 * @since 1.0.0
 */
export function add(a: number, b: number): number {
    return a + b;
}
'''
        result = extractor.extract(code, "math.ts")
        tsdoc = result.get('tsdoc', [])
        assert len(tsdoc) >= 1
        doc = tsdoc[0]
        assert len(doc.params) >= 1

    def test_tsdoc_deprecated(self, extractor):
        code = '''
/**
 * @deprecated Use `newMethod` instead.
 */
export function oldMethod(): void {}
'''
        result = extractor.extract(code, "legacy.ts")
        tsdoc = result.get('tsdoc', [])
        assert len(tsdoc) >= 1
        doc = tsdoc[0]
        assert doc.deprecated is not None and doc.deprecated != ""

    def test_tsdoc_template(self, extractor):
        code = '''
/**
 * Creates a typed repository.
 *
 * @template T - The entity type
 * @param entity - The entity class
 * @returns A new repository
 */
export function createRepository<T>(entity: new () => T): Repository<T> {
    return new Repository(entity);
}
'''
        result = extractor.extract(code, "factory.ts")
        tsdoc = result.get('tsdoc', [])
        assert len(tsdoc) >= 1
        doc = tsdoc[0]
        assert len(doc.template_params) >= 1
