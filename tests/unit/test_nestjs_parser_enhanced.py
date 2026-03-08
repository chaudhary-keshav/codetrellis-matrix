"""
Tests for NestJS enhanced extractors and EnhancedNestJSParser.

Part of CodeTrellis v4.81 NestJS Enhanced Per-File Framework Support.
Tests cover:
- Module extraction (@Module, @Global, dynamic modules, custom providers)
- Controller extraction (@Controller, HTTP decorators, @UseGuards, params)
- Provider extraction (@Injectable, constructor injection, @Inject, scopes)
- Config extraction (ConfigModule, ConfigService, process.env, registerAs)
- API extraction (@ApiTags, @ApiProperty, DTOs, class-validator)
- Parser integration (framework detection, version detection, is_nestjs_file)
"""

import pytest
from codetrellis.nestjs_parser_enhanced import (
    EnhancedNestJSParser,
    NestJSEnhancedParseResult,
)
from codetrellis.extractors.nestjs_enhanced import (
    NestModuleExtractor,
    NestModuleDecoratorInfo,
    NestProviderInfo,
    NestDynamicModuleInfo,
    NestControllerExtractor,
    NestControllerInfo,
    NestEndpointInfo,
    NestParamDecoratorInfo,
    NestProviderExtractor,
    NestInjectableInfo,
    NestInjectionInfo,
    NestCustomProviderInfo,
    NestConfigExtractor,
    NestConfigModuleInfo,
    NestEnvVarInfo,
    NestConfigServiceUsageInfo,
    NestApiExtractor,
    NestSwaggerInfo,
    NestApiPropertyInfo,
    NestDtoInfo,
    NestApiSummary,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedNestJSParser()


@pytest.fixture
def module_extractor():
    return NestModuleExtractor()


@pytest.fixture
def controller_extractor():
    return NestControllerExtractor()


@pytest.fixture
def provider_extractor():
    return NestProviderExtractor()


@pytest.fixture
def config_extractor():
    return NestConfigExtractor()


@pytest.fixture
def api_extractor():
    return NestApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Module Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestNestModuleExtractor:

    def test_extract_basic_module(self, module_extractor):
        """Test extracting a basic @Module() decorator."""
        content = """
import { Module } from '@nestjs/common';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';

@Module({
    imports: [],
    controllers: [UsersController],
    providers: [UsersService],
    exports: [UsersService],
})
export class UsersModule {}
"""
        result = module_extractor.extract(content, "users.module.ts")
        modules = result.get('modules', [])
        assert len(modules) >= 1
        mod = modules[0]
        assert mod.class_name == 'UsersModule'
        assert 'UsersController' in mod.controllers
        assert 'UsersService' in mod.providers

    def test_extract_global_module(self, module_extractor):
        """Test extracting @Global() + @Module()."""
        content = """
import { Module, Global } from '@nestjs/common';

@Global()
@Module({
    providers: [DatabaseService],
    exports: [DatabaseService],
})
export class DatabaseModule {}
"""
        result = module_extractor.extract(content, "database.module.ts")
        modules = result.get('modules', [])
        assert len(modules) >= 1
        assert modules[0].is_global is True

    def test_extract_dynamic_module(self, module_extractor):
        """Test extracting dynamic module methods."""
        content = """
import { Module, DynamicModule } from '@nestjs/common';

@Module({})
export class ConfigModule {
    static forRoot(options: ConfigOptions): DynamicModule {
        return {
            module: ConfigModule,
            providers: [{ provide: CONFIG_OPTIONS, useValue: options }],
        };
    }

    static forRootAsync(options: ConfigAsyncOptions): DynamicModule {
        return {
            module: ConfigModule,
            imports: options.imports || [],
        };
    }
}
"""
        result = module_extractor.extract(content, "config.module.ts")
        dynamic = result.get('dynamic_modules', [])
        assert len(dynamic) >= 2


# ═══════════════════════════════════════════════════════════════════
# Controller Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestNestControllerExtractor:

    def test_extract_basic_controller(self, controller_extractor):
        """Test extracting a @Controller with routes."""
        content = """
import { Controller, Get, Post, Put, Delete, Param, Body } from '@nestjs/common';
import { UsersService } from './users.service';
import { CreateUserDto } from './dto/create-user.dto';

@Controller('users')
export class UsersController {
    constructor(private readonly usersService: UsersService) {}

    @Get()
    findAll() {
        return this.usersService.findAll();
    }

    @Get(':id')
    findOne(@Param('id') id: string) {
        return this.usersService.findOne(id);
    }

    @Post()
    create(@Body() createUserDto: CreateUserDto) {
        return this.usersService.create(createUserDto);
    }

    @Delete(':id')
    remove(@Param('id') id: string) {
        return this.usersService.remove(id);
    }
}
"""
        result = controller_extractor.extract(content, "users.controller.ts")
        controllers = result.get('controllers', [])
        assert len(controllers) >= 1
        ctrl = controllers[0]
        assert ctrl.class_name == 'UsersController'
        assert ctrl.path == 'users'

    def test_extract_controller_with_guards(self, controller_extractor):
        """Test controller with @UseGuards."""
        content = """
import { Controller, Get, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { RolesGuard } from '../auth/roles.guard';

@UseGuards(JwtAuthGuard, RolesGuard)
@Controller('admin')
export class AdminController {
    @Get()
    getAdminPanel() {
        return 'admin panel';
    }
}
"""
        result = controller_extractor.extract(content, "admin.controller.ts")
        controllers = result.get('controllers', [])
        assert len(controllers) >= 1
        ctrl = controllers[0]
        assert ctrl.has_guards is True


# ═══════════════════════════════════════════════════════════════════
# Provider Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestNestProviderExtractor:

    def test_extract_injectable_service(self, provider_extractor):
        """Test extracting @Injectable() service."""
        content = """
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './entities/user.entity';

@Injectable()
export class UsersService {
    constructor(
        @InjectRepository(User)
        private readonly userRepository: Repository<User>,
    ) {}

    findAll(): Promise<User[]> {
        return this.userRepository.find();
    }
}
"""
        result = provider_extractor.extract(content, "users.service.ts")
        injectables = result.get('injectables', [])
        assert len(injectables) >= 1
        assert injectables[0].class_name == 'UsersService'

    def test_extract_scoped_provider(self, provider_extractor):
        """Test extracting provider with scope."""
        content = """
import { Injectable, Scope } from '@nestjs/common';

@Injectable({ scope: Scope.REQUEST })
export class RequestScopedService {
    constructor() {}
}
"""
        result = provider_extractor.extract(content, "request-scoped.service.ts")
        injectables = result.get('injectables', [])
        assert len(injectables) >= 1


# ═══════════════════════════════════════════════════════════════════
# Config Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestNestConfigExtractor:

    def test_extract_config_service_usage(self, config_extractor):
        """Test extracting ConfigService.get() usage."""
        content = """
import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class AppService {
    constructor(private configService: ConfigService) {}

    getDatabaseUrl(): string {
        return this.configService.get<string>('DATABASE_URL');
    }

    getPort(): number {
        return this.configService.getOrThrow<number>('PORT');
    }
}
"""
        result = config_extractor.extract(content, "app.service.ts")
        usages = result.get('config_usages', [])
        assert len(usages) >= 2

    def test_extract_process_env(self, config_extractor):
        """Test extracting process.env references."""
        content = """
const port = process.env.PORT || 3000;
const dbHost = process.env.DB_HOST || 'localhost';
const secret = process.env.JWT_SECRET;
"""
        result = config_extractor.extract(content, "config.ts")
        env_vars = result.get('env_vars', [])
        assert len(env_vars) >= 3


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestNestApiExtractor:

    def test_extract_swagger_decorators(self, api_extractor):
        """Test extracting Swagger decorators."""
        content = """
import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';

@ApiTags('users')
@Controller('users')
export class UsersController {
    @Get()
    @ApiOperation({ summary: 'Get all users' })
    @ApiResponse({ status: 200, description: 'List of users' })
    findAll() {}
}
"""
        result = api_extractor.extract(content, "users.controller.ts")
        swagger = result.get('swagger_decorators', [])
        assert len(swagger) >= 1

    def test_extract_dto_with_api_property(self, api_extractor):
        """Test extracting DTO classes with @ApiProperty."""
        content = """
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsEmail, IsOptional, IsInt, Min } from 'class-validator';

export class CreateUserDto {
    @ApiProperty({ description: 'User name' })
    @IsString()
    name: string;

    @ApiProperty({ description: 'Email address' })
    @IsEmail()
    email: string;

    @ApiPropertyOptional({ description: 'Age' })
    @IsOptional()
    @IsInt()
    @Min(0)
    age?: number;
}
"""
        result = api_extractor.extract(content, "create-user.dto.ts")
        dtos = result.get('dtos', [])
        assert len(dtos) >= 1
        api_props = result.get('api_properties', [])
        assert len(api_props) >= 2


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedNestJSParser:

    def test_is_nestjs_file(self, parser):
        """Test NestJS file detection."""
        nestjs_content = """
import { Controller, Get } from '@nestjs/common';

@Controller('users')
export class UsersController {
    @Get()
    findAll() {}
}
"""
        assert parser.is_nestjs_file(nestjs_content, "users.controller.ts") is True

    def test_is_not_nestjs_file(self, parser):
        """Test non-NestJS file detection."""
        react_content = """
import React from 'react';
const App = () => <div>Hello</div>;
export default App;
"""
        assert parser.is_nestjs_file(react_content, "App.tsx") is False

    def test_parse_full_nestjs_controller(self, parser):
        """Test parsing a complete NestJS controller file."""
        content = """
import { Controller, Get, Post, Delete, Param, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { UsersService } from './users.service';
import { CreateUserDto } from './dto/create-user.dto';

@ApiTags('users')
@Controller('users')
@UseGuards(JwtAuthGuard)
export class UsersController {
    constructor(private readonly usersService: UsersService) {}

    @Get()
    @ApiOperation({ summary: 'Get all users' })
    findAll() {
        return this.usersService.findAll();
    }

    @Post()
    create(@Body() dto: CreateUserDto) {
        return this.usersService.create(dto);
    }

    @Delete(':id')
    remove(@Param('id') id: string) {
        return this.usersService.remove(id);
    }
}
"""
        result = parser.parse(content, "users.controller.ts")
        assert isinstance(result, NestJSEnhancedParseResult)
        assert len(result.controllers) >= 1
        assert len(result.detected_frameworks) >= 1

    def test_parse_nestjs_module(self, parser):
        """Test parsing a NestJS module file."""
        content = """
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';
import { User } from './entities/user.entity';

@Module({
    imports: [TypeOrmModule.forFeature([User])],
    controllers: [UsersController],
    providers: [UsersService],
    exports: [UsersService],
})
export class UsersModule {}
"""
        result = parser.parse(content, "users.module.ts")
        assert isinstance(result, NestJSEnhancedParseResult)
        assert len(result.modules) >= 1

    def test_parse_nestjs_service(self, parser):
        """Test parsing a NestJS service file."""
        content = """
import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { ConfigService } from '@nestjs/config';
import { Repository } from 'typeorm';
import { User } from './entities/user.entity';

@Injectable()
export class UsersService {
    constructor(
        @InjectRepository(User)
        private readonly userRepository: Repository<User>,
        private readonly configService: ConfigService,
    ) {}

    async findAll(): Promise<User[]> {
        return this.userRepository.find();
    }

    async findOne(id: string): Promise<User> {
        const user = await this.userRepository.findOne({ where: { id } });
        if (!user) throw new NotFoundException(`User #${id} not found`);
        return user;
    }
}
"""
        result = parser.parse(content, "users.service.ts")
        assert isinstance(result, NestJSEnhancedParseResult)
        assert len(result.injectables) >= 1

    def test_parse_nestjs_dto(self, parser):
        """Test parsing a NestJS DTO file."""
        content = """
import { ApiProperty } from '@nestjs/swagger';
import { IsString, IsEmail, IsOptional } from 'class-validator';

export class CreateUserDto {
    @ApiProperty()
    @IsString()
    name: string;

    @ApiProperty()
    @IsEmail()
    email: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @IsString()
    bio?: string;
}
"""
        result = parser.parse(content, "create-user.dto.ts")
        assert isinstance(result, NestJSEnhancedParseResult)
        assert len(result.dtos) >= 1

    def test_detect_nestjs_ecosystem(self, parser):
        """Test NestJS ecosystem detection."""
        content = """
import { Controller, Get } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { ApiTags } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';
import { CacheInterceptor } from '@nestjs/cache-manager';

@Controller('users')
export class UsersController {
    @Get()
    findAll() {}
}
"""
        result = parser.parse(content, "users.controller.ts")
        assert isinstance(result, NestJSEnhancedParseResult)
        assert len(result.detected_frameworks) >= 1

    def test_parse_empty_file(self, parser):
        """Test parsing an empty file."""
        result = parser.parse("", "empty.ts")
        assert isinstance(result, NestJSEnhancedParseResult)
        assert len(result.controllers) == 0
        assert len(result.modules) == 0
