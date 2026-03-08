"""
Tests for TypeScriptAPIExtractor — NestJS, Express, Fastify, tRPC, GraphQL routes.

Part of CodeTrellis v4.31 TypeScript Language Support.
"""

import pytest
from codetrellis.extractors.typescript.api_extractor import (
    TypeScriptAPIExtractor,
    TSRouteInfo,
    TSMiddlewareInfo,
    TSWebSocketInfo,
    TSGraphQLResolverInfo,
    TSTRPCRouterInfo,
)


@pytest.fixture
def extractor():
    return TypeScriptAPIExtractor()


class TestNestJSRoutes:
    """Tests for NestJS route extraction."""

    def test_controller_routes(self, extractor):
        code = '''
@Controller('users')
export class UsersController {
    constructor(private readonly usersService: UsersService) {}

    @Get()
    findAll(): Promise<User[]> {
        return this.usersService.findAll();
    }

    @Get(':id')
    findOne(@Param('id') id: string): Promise<User> {
        return this.usersService.findOne(id);
    }

    @Post()
    create(@Body() dto: CreateUserDto): Promise<User> {
        return this.usersService.create(dto);
    }

    @Put(':id')
    update(@Param('id') id: string, @Body() dto: UpdateUserDto): Promise<User> {
        return this.usersService.update(id, dto);
    }

    @Delete(':id')
    remove(@Param('id') id: string): Promise<void> {
        return this.usersService.remove(id);
    }
}
'''
        result = extractor.extract(code, "users.controller.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 4

    def test_nestjs_guards(self, extractor):
        code = '''
@Controller('admin')
@UseGuards(JwtAuthGuard, RolesGuard)
export class AdminController {
    @Get('dashboard')
    @UseGuards(AdminGuard)
    getDashboard(): Promise<DashboardData> {
        return this.adminService.getDashboard();
    }
}
'''
        result = extractor.extract(code, "admin.controller.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 1


class TestExpressRoutes:
    """Tests for Express typed route extraction."""

    def test_express_typed_routes(self, extractor):
        code = '''
import { Router, Request, Response, NextFunction } from 'express';

const router = Router();

router.get('/users', async (req: Request, res: Response): Promise<void> => {
    const users = await UserService.findAll();
    res.json(users);
});

router.post('/users', async (req: Request<{}, {}, CreateUserDto>, res: Response): Promise<void> => {
    const user = await UserService.create(req.body);
    res.status(201).json(user);
});
'''
        result = extractor.extract(code, "users.routes.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 2


class TestFastifyRoutes:
    """Tests for Fastify typed route extraction."""

    def test_fastify_routes(self, extractor):
        code = '''
import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';

export async function userRoutes(app: FastifyInstance): Promise<void> {
    app.get<{ Reply: User[] }>('/users', async (request: FastifyRequest, reply: FastifyReply) => {
        return UserService.findAll();
    });

    app.post<{ Body: CreateUserDto; Reply: User }>('/users', async (request, reply) => {
        return UserService.create(request.body);
    });
}
'''
        result = extractor.extract(code, "users.routes.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 2


class TestMiddleware:
    """Tests for middleware extraction."""

    def test_nestjs_middleware(self, extractor):
        code = '''
@Injectable()
export class LoggerMiddleware implements NestMiddleware {
    use(req: Request, res: Response, next: NextFunction): void {
        console.log('Request...', req.method, req.url);
        next();
    }
}
'''
        result = extractor.extract(code, "logger.middleware.ts")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1
        mw = middleware[0]
        assert mw.name == "LoggerMiddleware"


class TestTRPCRoutes:
    """Tests for tRPC router extraction."""

    def test_trpc_router(self, extractor):
        code = '''
import { initTRPC } from '@trpc/server';

const t = initTRPC.create();

export const appRouter = t.router({
    getUser: t.procedure
        .input(z.object({ id: z.string() }))
        .query(async ({ input }) => {
            return getUserById(input.id);
        }),
    createUser: t.procedure
        .input(z.object({ name: z.string(), email: z.string() }))
        .mutation(async ({ input }) => {
            return createUser(input);
        }),
});
'''
        result = extractor.extract(code, "router.ts")
        trpc_routers = result.get('trpc_routers', [])
        assert len(trpc_routers) >= 1


class TestGraphQLResolvers:
    """Tests for GraphQL resolver extraction."""

    def test_type_graphql_resolver(self, extractor):
        code = '''
@Resolver(() => User)
export class UserResolver {
    @Query(() => [User])
    async users(): Promise<User[]> {
        return UserService.findAll();
    }

    @Mutation(() => User)
    async createUser(@Arg('input') input: CreateUserInput): Promise<User> {
        return UserService.create(input);
    }
}
'''
        result = extractor.extract(code, "user.resolver.ts")
        resolvers = result.get('graphql_resolvers', [])
        assert len(resolvers) >= 1


class TestWebSocket:
    """Tests for WebSocket extraction."""

    def test_nestjs_websocket_gateway(self, extractor):
        code = '''
@WebSocketGateway({ namespace: 'chat' })
export class ChatGateway {
    @SubscribeMessage('message')
    handleMessage(client: Socket, payload: MessageDto): void {
        this.server.emit('message', payload);
    }

    @SubscribeMessage('join')
    handleJoin(client: Socket, room: string): void {
        client.join(room);
    }
}
'''
        result = extractor.extract(code, "chat.gateway.ts")
        websockets = result.get('websockets', [])
        assert len(websockets) >= 1
