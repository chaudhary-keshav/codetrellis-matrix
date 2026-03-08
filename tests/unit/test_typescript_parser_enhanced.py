"""
Tests for EnhancedTypeScriptParser — full parser integration, framework detection, version detection.

Part of CodeTrellis v4.31 TypeScript Language Support.
"""

import pytest
from codetrellis.typescript_parser_enhanced import (
    EnhancedTypeScriptParser,
    TypeScriptParseResult,
)


@pytest.fixture
def parser():
    return EnhancedTypeScriptParser()


class TestParserIntegration:
    """Tests for full parser integration."""

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.ts")
        assert isinstance(result, TypeScriptParseResult)
        assert result.file_type == "typescript"
        assert len(result.classes) == 0

    def test_parse_declaration_file(self, parser):
        code = '''
declare module 'my-lib' {
    export interface Config {
        name: string;
        version: number;
    }

    export function init(config: Config): void;
}
'''
        result = parser.parse(code, "my-lib.d.ts")
        assert result.file_type == "dts"
        assert result.is_declaration_file is True

    def test_parse_tsx_file(self, parser):
        code = '''
import React, { useState } from 'react';

interface Props {
    title: string;
    count?: number;
}

export const Counter: React.FC<Props> = ({ title, count = 0 }) => {
    const [value, setValue] = useState(count);

    return (
        <div>
            <h1>{title}</h1>
            <p>{value}</p>
            <button onClick={() => setValue(v => v + 1)}>+</button>
        </div>
    );
};
'''
        result = parser.parse(code, "Counter.tsx")
        assert result.file_type == "tsx"
        assert len(result.interfaces) >= 1
        assert "react" in result.detected_frameworks

    def test_parse_mts_file(self, parser):
        result = parser.parse("export const x: number = 1;", "index.mts")
        assert result.file_type == "mts"

    def test_parse_cts_file(self, parser):
        result = parser.parse("export const x: number = 1;", "index.cts")
        assert result.file_type == "cts"


class TestFrameworkDetection:
    """Tests for framework detection."""

    def test_detect_nestjs(self, parser):
        code = '''
import { Controller, Get, Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
    getHello(): string {
        return 'Hello World!';
    }
}
'''
        result = parser.parse(code, "app.service.ts")
        assert "nestjs" in result.detected_frameworks

    def test_detect_angular(self, parser):
        code = '''
import { Component, OnInit, Input } from '@angular/core';

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
})
export class AppComponent implements OnInit {
    @Input() title = 'my-app';
    ngOnInit(): void {}
}
'''
        result = parser.parse(code, "app.component.ts")
        assert "angular" in result.detected_frameworks

    def test_detect_react(self, parser):
        code = '''
import React, { useState, useEffect } from 'react';

export const App: React.FC = () => {
    const [count, setCount] = useState(0);
    useEffect(() => { document.title = `Count: ${count}`; }, [count]);
    return <div>{count}</div>;
};
'''
        result = parser.parse(code, "App.tsx")
        assert "react" in result.detected_frameworks

    def test_detect_express(self, parser):
        code = '''
import express, { Request, Response, NextFunction } from 'express';

const app = express();

app.get('/api/users', (req: Request, res: Response) => {
    res.json([]);
});
'''
        result = parser.parse(code, "server.ts")
        assert "express" in result.detected_frameworks

    def test_detect_fastify(self, parser):
        code = '''
import Fastify, { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';

const app: FastifyInstance = Fastify();
'''
        result = parser.parse(code, "server.ts")
        assert "fastify" in result.detected_frameworks

    def test_detect_trpc(self, parser):
        code = '''
import { initTRPC, TRPCError } from '@trpc/server';

const t = initTRPC.create();
export const router = t.router;
export const publicProcedure = t.procedure;
'''
        result = parser.parse(code, "trpc.ts")
        assert "trpc" in result.detected_frameworks

    def test_detect_prisma(self, parser):
        code = '''
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function getUsers() {
    return prisma.user.findMany();
}
'''
        result = parser.parse(code, "db.ts")
        assert "prisma" in result.detected_frameworks

    def test_detect_typeorm(self, parser):
        code = '''
import { Entity, Column, PrimaryGeneratedColumn, Repository } from 'typeorm';

@Entity()
export class User {
    @PrimaryGeneratedColumn()
    id: number;
}
'''
        result = parser.parse(code, "user.entity.ts")
        assert "typeorm" in result.detected_frameworks

    def test_detect_zod(self, parser):
        code = '''
import { z } from 'zod';

export const UserSchema = z.object({
    name: z.string(),
    email: z.string().email(),
});
'''
        result = parser.parse(code, "schemas.ts")
        assert "zod" in result.detected_frameworks

    def test_detect_rxjs(self, parser):
        code = '''
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { map, filter, switchMap } from 'rxjs/operators';

const source$ = new BehaviorSubject<number>(0);
const doubled$ = source$.pipe(map(x => x * 2));
'''
        result = parser.parse(code, "streams.ts")
        assert "rxjs" in result.detected_frameworks

    def test_detect_vitest(self, parser):
        code = '''
import { describe, it, expect, vi } from 'vitest';

describe('math', () => {
    it('should add', () => {
        expect(1 + 1).toBe(2);
    });
});
'''
        result = parser.parse(code, "math.test.ts")
        assert "vitest" in result.detected_frameworks

    def test_detect_drizzle(self, parser):
        code = '''
import { pgTable, serial, text } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
    id: serial('id').primaryKey(),
    name: text('name'),
});
'''
        result = parser.parse(code, "schema.ts")
        assert "drizzle" in result.detected_frameworks

    def test_detect_nextjs(self, parser):
        code = '''
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    return NextResponse.json({ hello: 'world' });
}
'''
        result = parser.parse(code, "route.ts")
        assert "nextjs" in result.detected_frameworks

    def test_detect_multiple_frameworks(self, parser):
        code = '''
import { Controller, Get } from '@nestjs/common';
import { z } from 'zod';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const UserSchema = z.object({ name: z.string() });

@Controller('users')
export class UsersController {
    @Get()
    findAll() {}
}
'''
        result = parser.parse(code, "users.controller.ts")
        assert "nestjs" in result.detected_frameworks
        assert "zod" in result.detected_frameworks
        assert "prisma" in result.detected_frameworks


class TestVersionDetection:
    """Tests for TypeScript version detection."""

    def test_detect_ts_2_0(self, parser):
        code = '''
interface User {
    name: string;
}
enum Status {
    Active,
    Inactive
}
'''
        result = parser.parse(code, "types.ts")
        assert result.ts_version == "2.0"

    def test_detect_ts_2_1_mapped_types(self, parser):
        code = '''
type Readonly<T> = { readonly [P in keyof T]: T[P] };
'''
        result = parser.parse(code, "types.ts")
        assert result.ts_version == "2.1"

    def test_detect_ts_2_8_conditional_types(self, parser):
        code = '''
type IsString<T> = T extends string ? true : false;
'''
        result = parser.parse(code, "types.ts")
        assert result.ts_version == "2.8"

    def test_detect_ts_3_0_unknown(self, parser):
        code = '''
function process(input: unknown): string {
    if (typeof input === 'string') return input;
    return String(input);
}
'''
        result = parser.parse(code, "utils.ts")
        assert result.ts_version == "3.0"

    def test_detect_ts_3_7_optional_chaining(self, parser):
        code = '''
const name = user?.profile?.name;
const value = data ?? 'default';
'''
        result = parser.parse(code, "utils.ts")
        assert result.ts_version == "3.7"

    def test_detect_ts_4_1_template_literal(self, parser):
        code = '''
type EventName = `on${string}`;
'''
        result = parser.parse(code, "types.ts")
        assert result.ts_version == "4.1"

    def test_detect_ts_4_5_type_only_import_specifiers(self, parser):
        code = '''
import { type User, UserService } from './types';
'''
        result = parser.parse(code, "service.ts")
        assert result.ts_version == "4.5"

    def test_detect_ts_4_9_satisfies(self, parser):
        code = '''
const config = {
    host: 'localhost',
    port: 3000,
} satisfies ServerConfig;
'''
        result = parser.parse(code, "config.ts")
        assert result.ts_version == "4.9"

    def test_detect_ts_5_0_const_type_params(self, parser):
        code = '''
function createConfig<const T extends readonly string[]>(items: T): T {
    return items;
}
'''
        result = parser.parse(code, "utils.ts")
        assert result.ts_version == "5.0"

    def test_detect_ts_5_2_using(self, parser):
        code = '''
using handle = getResource();
'''
        result = parser.parse(code, "resources.ts")
        assert result.ts_version == "5.2"


class TestFullFileParsing:
    """Integration tests with complete TypeScript files."""

    def test_nestjs_service(self, parser):
        code = '''
import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import type { CreateUserDto } from './dto/create-user.dto';
import { User } from './entities/user.entity';

@Injectable()
export class UsersService {
    constructor(
        @InjectRepository(User)
        private readonly userRepository: Repository<User>,
    ) {}

    async findAll(): Promise<User[]> {
        return this.userRepository.find();
    }

    async findOne(id: number): Promise<User> {
        const user = await this.userRepository.findOneBy({ id });
        if (!user) {
            throw new NotFoundException(`User #${id} not found`);
        }
        return user;
    }

    async create(dto: CreateUserDto): Promise<User> {
        const user = this.userRepository.create(dto);
        return this.userRepository.save(user);
    }

    async remove(id: number): Promise<void> {
        await this.userRepository.delete(id);
    }
}
'''
        result = parser.parse(code, "users.service.ts")
        assert "nestjs" in result.detected_frameworks
        assert "typeorm" in result.detected_frameworks
        assert len(result.classes) >= 1
        assert len(result.imports) >= 3
        assert result.classes[0].name == "UsersService"

    def test_complex_types_file(self, parser):
        code = '''
// Complex TypeScript type definitions

export interface ApiResponse<T> {
    data: T;
    meta: {
        total: number;
        page: number;
        limit: number;
    };
    errors?: ApiError[];
}

export type Result<T, E = Error> = 
    | { success: true; data: T }
    | { success: false; error: E };

export type DeepPartial<T> = {
    [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export const enum LogLevel {
    Debug = 'DEBUG',
    Info = 'INFO',
    Warn = 'WARN',
    Error = 'ERROR',
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

export type EventHandler<T = void> = (event: T) => void | Promise<void>;

export abstract class BaseService<T extends { id: string }> {
    abstract findById(id: string): Promise<T>;
    abstract findAll(): Promise<T[]>;
    abstract create(data: Partial<T>): Promise<T>;
    abstract update(id: string, data: Partial<T>): Promise<T>;
    abstract delete(id: string): Promise<void>;
}
'''
        result = parser.parse(code, "types.ts")
        assert len(result.interfaces) >= 1
        assert len(result.type_aliases) >= 3
        assert len(result.enums) >= 1
        assert len(result.classes) >= 1
