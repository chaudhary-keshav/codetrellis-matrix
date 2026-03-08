"""
Tests for EnhancedJavaScriptParser — integrated parsing with all extractors.

Part of CodeTrellis v4.30 JavaScript Language Support.
"""

import pytest
from codetrellis.javascript_parser_enhanced import (
    EnhancedJavaScriptParser,
    JavaScriptParseResult,
)


@pytest.fixture
def parser():
    return EnhancedJavaScriptParser()


class TestFrameworkDetection:
    """Tests for framework detection (70+ frameworks)."""

    def test_express_detection(self, parser):
        code = '''
const express = require('express');
const app = express();

app.get('/api/users', (req, res) => {
    res.json([]);
});

app.listen(3000);
'''
        result = parser.parse(code, "server.js")
        assert "express" in result.detected_frameworks

    def test_react_detection(self, parser):
        code = '''
import React, { useState } from 'react';

function App() {
    const [count, setCount] = useState(0);
    return <div>{count}</div>;
}

export default App;
'''
        result = parser.parse(code, "App.jsx")
        assert "react" in result.detected_frameworks

    def test_fastify_detection(self, parser):
        code = '''
const fastify = require('fastify')();

fastify.get('/', async (request, reply) => {
    return { hello: 'world' };
});

fastify.listen({ port: 3000 });
'''
        result = parser.parse(code, "server.js")
        assert "fastify" in result.detected_frameworks

    def test_koa_detection(self, parser):
        code = '''
const Koa = require('koa');
const app = new Koa();

app.use(async ctx => {
    ctx.body = 'Hello World';
});
'''
        result = parser.parse(code, "app.js")
        assert "koa" in result.detected_frameworks

    def test_mongoose_detection(self, parser):
        code = '''
const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
    name: String,
    email: String,
});

module.exports = mongoose.model('User', userSchema);
'''
        result = parser.parse(code, "user.model.js")
        assert "mongoose" in result.detected_frameworks

    def test_jest_detection(self, parser):
        code = '''
describe('Calculator', () => {
    test('adds two numbers', () => {
        expect(add(2, 3)).toBe(5);
    });

    it('subtracts two numbers', () => {
        expect(subtract(5, 3)).toBe(2);
    });
});
'''
        result = parser.parse(code, "calc.test.js")
        assert "jest" in result.detected_frameworks

    def test_socket_io_detection(self, parser):
        code = '''
const { Server } = require('socket.io');
const io = new Server(server);

io.on('connection', (socket) => {
    socket.on('chat message', (msg) => {
        io.emit('chat message', msg);
    });
});
'''
        result = parser.parse(code, "socket.js")
        assert "socketio" in result.detected_frameworks

    def test_redux_detection(self, parser):
        code = '''
import { createSlice, configureStore } from '@reduxjs/toolkit';

const counterSlice = createSlice({
    name: 'counter',
    initialState: { value: 0 },
    reducers: {
        increment: state => { state.value += 1; },
    },
});
'''
        result = parser.parse(code, "store.js")
        assert "redux" in result.detected_frameworks

    def test_multiple_frameworks(self, parser):
        code = '''
const express = require('express');
const mongoose = require('mongoose');
const passport = require('passport');
const jwt = require('jsonwebtoken');

const app = express();
'''
        result = parser.parse(code, "app.js")
        assert len(result.detected_frameworks) >= 3

    def test_nextjs_detection(self, parser):
        code = '''
import { NextResponse } from 'next/server';

export async function GET(request) {
    return NextResponse.json({ hello: 'world' });
}
'''
        result = parser.parse(code, "route.js")
        assert "nextjs" in result.detected_frameworks

    def test_prisma_detection(self, parser):
        code = '''
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function getUsers() {
    return prisma.user.findMany();
}
'''
        result = parser.parse(code, "db.js")
        assert "prisma" in result.detected_frameworks


class TestVersionDetection:
    """Tests for JavaScript version detection."""

    def test_es6_detection(self, parser):
        code = '''
import { something } from './module';
const fn = () => {};
class MyClass {}
'''
        result = parser.parse(code, "es6.js")
        assert result.js_version in ["ES6", "ES2015", "ES2017", "ES2018", "ES2020", "ES2022", "ES2024"]

    def test_es2020_optional_chaining(self, parser):
        code = '''
const name = user?.profile?.name;
const value = data ?? 'default';
'''
        result = parser.parse(code, "es2020.js")
        assert result.js_version in ["ES2020", "ES2022", "ES2024"]

    def test_es2022_private_fields(self, parser):
        code = '''
class Counter {
    #count = 0;

    increment() {
        this.#count++;
    }
}
'''
        result = parser.parse(code, "es2022.js")
        assert result.js_version in ["ES2022", "ES2024"]


class TestModuleSystem:
    """Tests for module system detection."""

    def test_esm_detection(self, parser):
        code = '''
import express from 'express';
export const app = express();
export default app;
'''
        result = parser.parse(code, "app.mjs")
        assert result.module_system == "esm"

    def test_commonjs_detection(self, parser):
        code = '''
const express = require('express');
const app = express();
module.exports = app;
'''
        result = parser.parse(code, "app.cjs")
        assert result.module_system == "commonjs"

    def test_mixed_module_system(self, parser):
        code = '''
import config from './config';
const legacy = require('./legacy');
export default config;
'''
        result = parser.parse(code, "mixed.js")
        assert result.module_system == "mixed"


class TestIntegratedParsing:
    """Tests for integrated parsing with all extractors."""

    def test_full_express_app(self, parser):
        code = '''
const express = require('express');
const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
    name: { type: String, required: true },
    email: { type: String, unique: true },
});

const User = mongoose.model('User', userSchema);

class UserService {
    async findAll() {
        return User.find();
    }

    async create(data) {
        return User.create(data);
    }
}

const router = express.Router();

router.get('/users', async (req, res) => {
    const service = new UserService();
    const users = await service.findAll();
    res.json(users);
});

router.post('/users', async (req, res) => {
    const service = new UserService();
    const user = await service.create(req.body);
    res.status(201).json(user);
});

module.exports = router;
'''
        result = parser.parse(code, "users.js")

        # Should detect frameworks
        assert len(result.detected_frameworks) >= 2

        # Should extract classes
        assert len(result.classes) >= 1

        # Should extract routes
        assert len(result.routes) >= 2

        # Should extract models
        assert len(result.models) >= 1

        # Should detect CommonJS module system
        assert result.module_system == "commonjs"

    def test_react_component(self, parser):
        code = '''
import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * User list component with pagination.
 * @param {Object} props - Component props
 * @returns {JSX.Element} Rendered component
 */
const UserList = ({ pageSize = 10 }) => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchUsers = async () => {
            const { data } = await axios.get('/api/users');
            setUsers(data);
            setLoading(false);
        };
        fetchUsers();
    }, []);

    if (loading) return <div>Loading...</div>;

    return (
        <ul>
            {users.map(user => (
                <li key={user.id}>{user.name}</li>
            ))}
        </ul>
    );
};

export default UserList;
'''
        result = parser.parse(code, "UserList.jsx")

        # Should detect React
        assert "react" in result.detected_frameworks

        # Should extract imports
        assert len(result.imports) >= 2

        # Should extract arrow functions
        assert len(result.arrow_functions) >= 1

        # Should extract JSDoc
        assert len(result.jsdoc) >= 1

        # Should detect ESM
        assert result.module_system == "esm"

    def test_empty_file(self, parser):
        result = parser.parse("", "empty.js")
        assert len(result.classes) == 0
        assert len(result.functions) == 0
        assert len(result.routes) == 0

    def test_comment_only_file(self, parser):
        code = '''
// This is just a comment file
/* Nothing else here */
'''
        result = parser.parse(code, "comment.js")
        # Should not crash
        assert isinstance(result, JavaScriptParseResult)

    def test_parse_result_structure(self, parser):
        code = 'const x = 1;'
        result = parser.parse(code, "minimal.js")
        assert result.file_path == "minimal.js"
        assert result.file_type == "javascript"
        assert isinstance(result.classes, list)
        assert isinstance(result.functions, list)
        assert isinstance(result.routes, list)
        assert isinstance(result.imports, list)
        assert isinstance(result.exports, list)
        assert isinstance(result.detected_frameworks, list)
