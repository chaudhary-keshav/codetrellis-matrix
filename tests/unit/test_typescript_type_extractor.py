"""
Tests for TypeScriptTypeExtractor — class, interface, type alias, enum extraction.

Part of CodeTrellis v4.31 TypeScript Language Support.
"""

import pytest
from codetrellis.extractors.typescript.type_extractor import (
    TypeScriptTypeExtractor,
    TSClassInfo,
    TSInterfaceInfo,
    TSTypeAliasInfo,
    TSEnumInfo,
    TSPropertyInfo,
    TSGenericParam,
)


@pytest.fixture
def extractor():
    return TypeScriptTypeExtractor()


class TestClassExtraction:
    """Tests for TypeScript class extraction."""

    def test_simple_class(self, extractor):
        code = '''
export class UserService {
    private db: Database;

    constructor(db: Database) {
        this.db = db;
    }

    async findById(id: string): Promise<User> {
        return this.db.find(id);
    }
}
'''
        result = extractor.extract(code, "service.ts")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "UserService"
        assert cls.is_exported is True

    def test_abstract_class(self, extractor):
        code = '''
export abstract class BaseEntity {
    id: string;
    createdAt: Date;

    abstract validate(): boolean;

    save(): void {}
}
'''
        result = extractor.extract(code, "entity.ts")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "BaseEntity"
        assert cls.is_abstract is True

    def test_class_with_implements(self, extractor):
        code = '''
export class AuthService implements IAuthService, IDisposable {
    login(credentials: Credentials): Promise<Token> {
        return this.authenticate(credentials);
    }

    dispose(): void {}
}
'''
        result = extractor.extract(code, "auth.ts")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "AuthService"
        assert "IAuthService" in cls.implements or len(cls.implements) >= 1

    def test_class_with_generics(self, extractor):
        code = '''
export class Repository<T extends BaseEntity> {
    private items: T[] = [];

    add(item: T): void {
        this.items.push(item);
    }

    findAll(): T[] {
        return this.items;
    }
}
'''
        result = extractor.extract(code, "repository.ts")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "Repository"
        assert len(cls.generics) >= 1

    def test_class_with_decorators(self, extractor):
        code = '''
@Injectable()
@Controller('users')
export class UsersController {
    constructor(private readonly usersService: UsersService) {}

    @Get()
    findAll(): Promise<User[]> {
        return this.usersService.findAll();
    }
}
'''
        result = extractor.extract(code, "users.controller.ts")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "UsersController"
        assert len(cls.decorators) >= 1

    def test_class_with_access_modifiers(self, extractor):
        code = '''
export class Config {
    public name: string;
    private secret: string;
    protected base: string;
    readonly version: number = 1;

    public getSecret(): string {
        return this.secret;
    }

    private validate(): boolean {
        return true;
    }

    protected reset(): void {}
}
'''
        result = extractor.extract(code, "config.ts")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "Config"
        # Should have both public, private, and protected methods
        assert len(cls.methods) >= 1 or len(cls.private_methods) >= 1 or len(cls.protected_methods) >= 1


class TestInterfaceExtraction:
    """Tests for TypeScript interface extraction."""

    def test_simple_interface(self, extractor):
        code = '''
export interface User {
    id: string;
    name: string;
    email: string;
    age?: number;
}
'''
        result = extractor.extract(code, "types.ts")
        interfaces = result.get('interfaces', [])
        assert len(interfaces) >= 1
        iface = interfaces[0]
        assert iface.name == "User"
        assert iface.is_exported is True
        assert len(iface.properties) >= 3

    def test_interface_with_extends(self, extractor):
        code = '''
interface Timestamped {
    createdAt: Date;
    updatedAt: Date;
}

export interface User extends Timestamped {
    id: string;
    name: string;
}
'''
        result = extractor.extract(code, "types.ts")
        interfaces = result.get('interfaces', [])
        user_ifaces = [i for i in interfaces if i.name == "User"]
        assert len(user_ifaces) >= 1
        assert len(user_ifaces[0].extends) >= 1

    def test_interface_with_generics(self, extractor):
        code = '''
export interface Repository<T> {
    findById(id: string): Promise<T>;
    findAll(): Promise<T[]>;
    save(entity: T): Promise<T>;
    delete(id: string): Promise<void>;
}
'''
        result = extractor.extract(code, "repository.ts")
        interfaces = result.get('interfaces', [])
        assert len(interfaces) >= 1
        iface = interfaces[0]
        assert iface.name == "Repository"
        assert len(iface.generics) >= 1

    def test_interface_with_index_signature(self, extractor):
        code = '''
export interface StringMap {
    [key: string]: string;
}
'''
        result = extractor.extract(code, "types.ts")
        interfaces = result.get('interfaces', [])
        assert len(interfaces) >= 1
        assert interfaces[0].name == "StringMap"

    def test_interface_with_methods(self, extractor):
        code = '''
export interface Logger {
    info(message: string): void;
    warn(message: string): void;
    error(message: string, stack?: string): void;
}
'''
        result = extractor.extract(code, "logger.ts")
        interfaces = result.get('interfaces', [])
        assert len(interfaces) >= 1
        iface = interfaces[0]
        assert iface.name == "Logger"
        assert len(iface.methods) >= 2


class TestTypeAliasExtraction:
    """Tests for TypeScript type alias extraction."""

    def test_union_type(self, extractor):
        code = '''
export type Status = 'active' | 'inactive' | 'pending';
'''
        result = extractor.extract(code, "types.ts")
        aliases = result.get('type_aliases', [])
        assert len(aliases) >= 1
        assert aliases[0].name == "Status"
        assert aliases[0].kind == "union"

    def test_intersection_type(self, extractor):
        code = '''
export type WithTimestamps = BaseEntity & { createdAt: Date; updatedAt: Date };
'''
        result = extractor.extract(code, "types.ts")
        aliases = result.get('type_aliases', [])
        assert len(aliases) >= 1
        assert aliases[0].name == "WithTimestamps"
        assert aliases[0].kind == "intersection"

    def test_conditional_type(self, extractor):
        code = '''
export type IsString<T> = T extends string ? true : false;
'''
        result = extractor.extract(code, "types.ts")
        aliases = result.get('type_aliases', [])
        assert len(aliases) >= 1
        assert aliases[0].name == "IsString"
        assert aliases[0].kind == "conditional"

    def test_mapped_type(self, extractor):
        code = '''
export type MyReadonly<T> = { readonly [P in keyof T]: T[P] };
'''
        result = extractor.extract(code, "types.ts")
        aliases = result.get('type_aliases', [])
        assert len(aliases) >= 1
        assert aliases[0].name == "MyReadonly"
        assert aliases[0].kind == "mapped"

    def test_template_literal_type(self, extractor):
        code = '''
export type EventName = `on${string}`;
'''
        result = extractor.extract(code, "types.ts")
        aliases = result.get('type_aliases', [])
        assert len(aliases) >= 1
        assert aliases[0].name == "EventName"
        assert aliases[0].kind == "template_literal"

    def test_utility_type(self, extractor):
        code = '''
export type UserInput = Partial<User>;
'''
        result = extractor.extract(code, "types.ts")
        aliases = result.get('type_aliases', [])
        assert len(aliases) >= 1
        assert aliases[0].name == "UserInput"
        assert aliases[0].kind == "utility"

    def test_generic_type_alias(self, extractor):
        code = '''
export type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };
'''
        result = extractor.extract(code, "types.ts")
        aliases = result.get('type_aliases', [])
        assert len(aliases) >= 1
        assert aliases[0].name == "Result"


class TestEnumExtraction:
    """Tests for TypeScript enum extraction."""

    def test_string_enum(self, extractor):
        code = '''
export enum Direction {
    Up = "UP",
    Down = "DOWN",
    Left = "LEFT",
    Right = "RIGHT"
}
'''
        result = extractor.extract(code, "types.ts")
        enums = result.get('enums', [])
        assert len(enums) >= 1
        enum = enums[0]
        assert enum.name == "Direction"
        assert len(enum.members) >= 4
        assert enum.is_exported is True

    def test_numeric_enum(self, extractor):
        code = '''
enum HttpStatus {
    OK = 200,
    NotFound = 404,
    InternalServerError = 500
}
'''
        result = extractor.extract(code, "types.ts")
        enums = result.get('enums', [])
        assert len(enums) >= 1
        assert enums[0].name == "HttpStatus"

    def test_const_enum(self, extractor):
        code = '''
export const enum Color {
    Red,
    Green,
    Blue
}
'''
        result = extractor.extract(code, "types.ts")
        enums = result.get('enums', [])
        assert len(enums) >= 1
        enum = enums[0]
        assert enum.name == "Color"
        assert enum.is_const is True

    def test_ambient_enum(self, extractor):
        code = '''
declare enum ExternalEnum {
    A,
    B,
    C
}
'''
        result = extractor.extract(code, "types.d.ts")
        enums = result.get('enums', [])
        assert len(enums) >= 1
        assert enums[0].is_ambient is True
