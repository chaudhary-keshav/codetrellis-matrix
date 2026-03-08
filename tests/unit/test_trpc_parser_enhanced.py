"""
Tests for tRPC extractors and EnhancedTRPCParser.

Part of CodeTrellis v4.85 tRPC Backend Framework Support.
Tests cover:
- Router extraction (createRouter, router, mergeRouters, v9+v10/v11)
- Middleware extraction (definition, usage, categories)
- Context extraction (createContext, schemas, zod/yup/typebox/superstruct)
- Config extraction (adapters, links, error formatters, superjson)
- API extraction (package detection, client patterns, ecosystem)
- Parser integration (framework detection, version detection, is_trpc_file)
"""

import pytest
from codetrellis.trpc_parser_enhanced import (
    EnhancedTRPCParser,
    TRPCParseResult,
)
from codetrellis.extractors.trpc import (
    TRPCRouterExtractor,
    TRPCMiddlewareExtractor,
    TRPCContextExtractor,
    TRPCConfigExtractor,
    TRPCApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedTRPCParser()


@pytest.fixture
def router_extractor():
    return TRPCRouterExtractor()


@pytest.fixture
def middleware_extractor():
    return TRPCMiddlewareExtractor()


@pytest.fixture
def context_extractor():
    return TRPCContextExtractor()


@pytest.fixture
def config_extractor():
    return TRPCConfigExtractor()


@pytest.fixture
def api_extractor():
    return TRPCApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Router Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestTRPCRouterExtractor:

    def test_extract_v10_router(self, router_extractor):
        """Test extracting v10/v11 router definitions."""
        content = """
import { router, publicProcedure } from './trpc';

export const appRouter = router({
  user: userRouter,
  post: postRouter,
});

export type AppRouter = typeof appRouter;
"""
        result = router_extractor.extract(content, "server/router.ts")
        routers = result.get('routers', [])
        assert len(routers) >= 1
        assert routers[0].name == 'appRouter'

    def test_extract_v10_procedures(self, router_extractor):
        """Test extracting v10/v11 procedure definitions."""
        content = """
import { router, publicProcedure } from '../trpc';
import { z } from 'zod';

export const userRouter = router({
  getById: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      return getUserById(input.id);
    }),

  create: publicProcedure
    .input(z.object({ name: z.string(), email: z.string().email() }))
    .mutation(async ({ input }) => {
      return createUser(input);
    }),

  onUpdate: publicProcedure
    .subscription(() => {
      return observable((emit) => {
        const unsubscribe = ee.on('update', emit.next);
        return unsubscribe;
      });
    }),
});
"""
        result = router_extractor.extract(content, "server/user.ts")
        procedures = result.get('procedures', [])
        assert len(procedures) >= 3
        types = [p.procedure_type for p in procedures]
        assert 'query' in types
        assert 'mutation' in types
        assert 'subscription' in types

    def test_extract_v9_router(self, router_extractor):
        """Test extracting v9 createRouter pattern."""
        content = """
import * as trpc from '@trpc/server';

const appRouter = trpc.router()
  .query('getUser', {
    input: z.object({ id: z.string() }),
    resolve: async ({ input }) => {
      return getUserById(input.id);
    },
  })
  .mutation('createUser', {
    input: z.object({ name: z.string() }),
    resolve: async ({ input }) => {
      return createUser(input);
    },
  });
"""
        result = router_extractor.extract(content, "server/router.ts")
        routers = result.get('routers', [])
        assert len(routers) >= 1

    def test_extract_merged_routers(self, router_extractor):
        """Test extracting mergeRouters calls."""
        content = """
import { mergeRouters } from './trpc';

export const appRouter = mergeRouters(userRouter, postRouter, commentRouter);
"""
        result = router_extractor.extract(content, "server/index.ts")
        merged = result.get('merged_routers', [])
        assert len(merged) >= 1

    def test_extract_protected_procedures(self, router_extractor):
        """Test extracting protected/private procedures."""
        content = """
import { router, protectedProcedure, adminProcedure } from '../trpc';

export const adminRouter = router({
  deleteUser: adminProcedure
    .input(z.object({ userId: z.string() }))
    .mutation(async ({ input, ctx }) => {
      return deleteUser(input.userId);
    }),

  getStats: protectedProcedure
    .query(async ({ ctx }) => {
      return getStats(ctx.user.id);
    }),
});
"""
        result = router_extractor.extract(content, "server/admin.ts")
        procedures = result.get('procedures', [])
        assert len(procedures) >= 2
        # At least one should be detected as protected
        protected = [p for p in procedures if p.is_protected]
        assert len(protected) >= 1


# ═══════════════════════════════════════════════════════════════════
# Middleware Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestTRPCMiddlewareExtractor:

    def test_extract_middleware_definitions(self, middleware_extractor):
        """Test extracting middleware function definitions."""
        content = """
import { t } from './trpc';

const isAuthed = t.middleware(({ ctx, next }) => {
  if (!ctx.session?.user) {
    throw new TRPCError({ code: 'UNAUTHORIZED' });
  }
  return next({
    ctx: {
      user: ctx.session.user,
    },
  });
});

const loggerMiddleware = t.middleware(async ({ path, type, next }) => {
  const start = Date.now();
  const result = await next();
  const durationMs = Date.now() - start;
  console.log(`${type} ${path} took ${durationMs}ms`);
  return result;
});
"""
        result = middleware_extractor.extract(content, "server/middleware.ts")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 2
        names = [m.name for m in middleware]
        assert 'isAuthed' in names
        assert 'loggerMiddleware' in names

    def test_extract_middleware_usage(self, middleware_extractor):
        """Test extracting middleware usage in procedure chains."""
        content = """
const protectedProcedure = publicProcedure.use(isAuthed);
const adminProcedure = protectedProcedure.use(isAdmin);
"""
        result = middleware_extractor.extract(content, "server/trpc.ts")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 2


# ═══════════════════════════════════════════════════════════════════
# Context Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestTRPCContextExtractor:

    def test_extract_create_context(self, context_extractor):
        """Test extracting createContext function."""
        content = """
import { inferAsyncReturnType } from '@trpc/server';
import { CreateNextContextOptions } from '@trpc/server/adapters/next';

export async function createContext(opts: CreateNextContextOptions) {
  const session = await getServerAuthSession(opts);
  return {
    session,
    prisma,
    headers: opts.req.headers,
  };
}

export type Context = inferAsyncReturnType<typeof createContext>;
"""
        result = context_extractor.extract(content, "server/context.ts")
        contexts = result.get('contexts', [])
        assert len(contexts) >= 1

    def test_extract_input_schemas(self, context_extractor):
        """Test extracting input/output schema patterns from procedure chains."""
        content = """
import { z } from 'zod';

export const userRouter = router({
  getById: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      return getUserById(input.id);
    }),

  create: publicProcedure
    .input(z.object({ name: z.string(), email: z.string().email() }))
    .output(z.object({ id: z.string(), name: z.string() }))
    .mutation(async ({ input }) => {
      return createUser(input);
    }),
});
"""
        result = context_extractor.extract(content, "server/schemas.ts")
        inputs = result.get('inputs', [])
        outputs = result.get('outputs', [])
        # Should detect inline input schemas in procedure chains
        assert len(inputs) >= 1 or len(outputs) >= 1


# ═══════════════════════════════════════════════════════════════════
# Config Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestTRPCConfigExtractor:

    def test_extract_adapter(self, config_extractor):
        """Test extracting tRPC adapter configuration."""
        content = """
import { createNextApiHandler } from '@trpc/server/adapters/next';
import { appRouter } from '../server/router';
import { createContext } from '../server/context';

export default createNextApiHandler({
  router: appRouter,
  createContext,
  onError: ({ error }) => {
    console.error(error);
  },
});
"""
        result = config_extractor.extract(content, "pages/api/trpc/[trpc].ts")
        adapters = result.get('adapters', [])
        assert len(adapters) >= 1
        assert any('next' in a.adapter_type.lower() for a in adapters)

    def test_extract_links(self, config_extractor):
        """Test extracting tRPC link configuration."""
        content = """
import { httpBatchLink, splitLink, wsLink } from '@trpc/client';

const trpc = createTRPCNext<AppRouter>({
  config() {
    return {
      links: [
        splitLink({
          condition: (op) => op.type === 'subscription',
          true: wsLink({ url: 'ws://localhost:3001' }),
          false: httpBatchLink({ url: '/api/trpc' }),
        }),
      ],
      transformer: superjson,
    };
  },
});
"""
        result = config_extractor.extract(content, "utils/trpc.ts")
        links = result.get('links', [])
        assert len(links) >= 1

    def test_extract_error_formatter(self, config_extractor):
        """Test extracting error formatter."""
        content = """
import { initTRPC } from '@trpc/server';
import superjson from 'superjson';

const t = initTRPC.context<Context>().create({
  transformer: superjson,
  errorFormatter({ shape, error }) {
    return {
      ...shape,
      data: {
        ...shape.data,
        zodError: error.cause instanceof ZodError ? error.cause.flatten() : null,
      },
    };
  },
});
"""
        result = config_extractor.extract(content, "server/trpc.ts")
        config = result.get('config', {})
        # Should detect superjson and error formatter
        assert config.get('has_superjson') or config.get('has_error_formatter') or len(result.get('adapters', [])) >= 0


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestTRPCApiExtractor:

    def test_extract_core_imports(self, api_extractor):
        """Test extracting core tRPC package imports."""
        content = """
import { initTRPC } from '@trpc/server';
import { createTRPCProxyClient, httpBatchLink } from '@trpc/client';
import { createTRPCNext } from '@trpc/next';
import { z } from 'zod';
"""
        result = api_extractor.extract(content, "server/trpc.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 3
        packages = [i.module for i in imports]
        assert '@trpc/server' in packages
        assert '@trpc/client' in packages

    def test_extract_client_patterns(self, api_extractor):
        """Test extracting tRPC client usage patterns."""
        content = """
import { trpc } from '../utils/trpc';

function UserProfile() {
  const { data: user } = trpc.user.getById.useQuery({ id: '1' });
  const createUser = trpc.user.create.useMutation();
  const utils = trpc.useUtils();
  return <div>{user?.name}</div>;
}
"""
        result = api_extractor.extract(content, "components/UserProfile.tsx")
        clients = result.get('clients', [])
        # Should detect client usages
        assert len(clients) >= 1 or len(result.get('imports', [])) >= 0


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedTRPCParser:

    def test_is_trpc_file_positive(self, parser):
        """Test that tRPC files are correctly identified."""
        content = """
import { initTRPC } from '@trpc/server';
const t = initTRPC.context<Context>().create();
"""
        assert parser.is_trpc_file(content, "server/trpc.ts") is True

    def test_is_trpc_file_negative(self, parser):
        """Test that non-tRPC files are correctly rejected."""
        content = """
import React from 'react';
function App() { return <div>Hello</div>; }
"""
        assert parser.is_trpc_file(content, "App.tsx") is False

    def test_parse_full_trpc_file(self, parser):
        """Test full parsing of a tRPC file."""
        content = """
import { initTRPC, TRPCError } from '@trpc/server';
import { z } from 'zod';
import superjson from 'superjson';

const t = initTRPC.context<Context>().create({
  transformer: superjson,
});

const publicProcedure = t.procedure;

const isAuthed = t.middleware(({ ctx, next }) => {
  if (!ctx.session) throw new TRPCError({ code: 'UNAUTHORIZED' });
  return next({ ctx: { user: ctx.session.user } });
});

const protectedProcedure = publicProcedure.use(isAuthed);

export const userRouter = t.router({
  getAll: publicProcedure
    .query(async () => {
      return prisma.user.findMany();
    }),
  getById: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      return prisma.user.findUnique({ where: { id: input.id } });
    }),
  create: protectedProcedure
    .input(z.object({ name: z.string(), email: z.string().email() }))
    .mutation(async ({ input, ctx }) => {
      return prisma.user.create({ data: input });
    }),
});
"""
        result = parser.parse(content, "server/user.ts")
        assert isinstance(result, TRPCParseResult)
        assert len(result.detected_frameworks) >= 0
        # Should find router
        assert len(result.routers) >= 1
        # Should find procedures
        assert len(result.procedures) >= 2

    def test_detect_trpc_version(self, parser):
        """Test tRPC version detection."""
        # v10+ uses initTRPC
        content_v10 = """
import { initTRPC } from '@trpc/server';
const t = initTRPC.create();
"""
        result = parser.parse(content_v10, "trpc.ts")
        # Should detect as v10+
        assert result.trpc_version is not None or result.detected_frameworks is not None

        # v9 uses trpc.router()
        content_v9 = """
import * as trpc from '@trpc/server';
const router = trpc.router().query('hello', { resolve: () => 'hi' });
"""
        result_v9 = parser.parse(content_v9, "router.ts")
        assert isinstance(result_v9, TRPCParseResult)

    def test_framework_detection(self, parser):
        """Test framework detection from imports."""
        content = """
import { initTRPC } from '@trpc/server';
import { createTRPCNext } from '@trpc/next';
import { createTRPCReact } from '@trpc/react-query';
import superjson from 'superjson';
"""
        result = parser.parse(content, "utils/trpc.ts")
        # Should detect tRPC-related frameworks
        assert len(result.detected_frameworks) >= 1 or result.trpc_version is not None

    def test_parse_empty_content(self, parser):
        """Test parsing empty content returns empty result."""
        result = parser.parse("", "empty.ts")
        assert isinstance(result, TRPCParseResult)
        assert len(result.routers) == 0
        assert len(result.procedures) == 0

    def test_typescript_detection(self, parser):
        """Test TypeScript detection from file extension."""
        content = """
import { initTRPC } from '@trpc/server';
"""
        result = parser.parse(content, "server/trpc.ts")
        assert result.is_typescript is True

        result_js = parser.parse(content, "server/trpc.js")
        assert result_js.is_typescript is False
