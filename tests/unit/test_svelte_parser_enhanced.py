"""
Tests for Svelte/SvelteKit extractors and EnhancedSvelteParser.

Part of CodeTrellis v4.35 Svelte/SvelteKit Language Support.
Tests cover:
- Component extraction (props, events, slots, bindings, transitions, actions, runes)
- Store extraction (writable, readable, derived, custom stores, subscriptions)
- Action extraction (use: directives, update/destroy lifecycle)
- Routing extraction (SvelteKit routes, load functions, form actions, hooks, param matchers)
- Lifecycle extraction (lifecycle hooks, context API, Svelte 5 runes)
- Parser integration (framework detection, version detection, file type detection)
"""

import pytest
from codetrellis.svelte_parser_enhanced import (
    EnhancedSvelteParser,
    SvelteParseResult,
)
from codetrellis.extractors.svelte import (
    SvelteComponentExtractor,
    SvelteStoreExtractor,
    SvelteActionExtractor,
    SvelteRoutingExtractor,
    SvelteLifecycleExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedSvelteParser()


@pytest.fixture
def component_extractor():
    return SvelteComponentExtractor()


@pytest.fixture
def store_extractor():
    return SvelteStoreExtractor()


@pytest.fixture
def action_extractor():
    return SvelteActionExtractor()


@pytest.fixture
def routing_extractor():
    return SvelteRoutingExtractor()


@pytest.fixture
def lifecycle_extractor():
    return SvelteLifecycleExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSvelteComponentExtractor:
    """Tests for SvelteComponentExtractor."""

    def test_svelte5_runes_component(self, component_extractor):
        """Test Svelte 5 component with runes."""
        code = '''
<script lang="ts">
let count = $state(0)
let doubled = $derived(count * 2)

$effect(() => {
    console.log(`Count: ${count}`)
})

interface Props {
    title: string
    onClose: () => void
}

let { title, onClose }: Props = $props()
</script>

<h1>{title}</h1>
<button onclick={() => count++}>{count} (doubled: {doubled})</button>

<style>
h1 { color: red; }
</style>
'''
        result = component_extractor.extract(code, "Counter.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.has_script
        assert comp.has_style
        assert comp.script_lang == "ts"
        assert comp.uses_runes

    def test_svelte4_export_let_props(self, component_extractor):
        """Test Svelte 3/4 export let props."""
        code = '''
<script>
export let name = 'World';
export let count = 0;
export let items = [];
</script>

<h1>Hello {name}!</h1>
<p>Count: {count}</p>
'''
        result = component_extractor.extract(code, "Greeting.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.has_script
        assert len(comp.props) >= 3

    def test_snippet_detection(self, component_extractor):
        """Test Svelte 5 snippets detection."""
        code = '''
<script lang="ts">
import type { Snippet } from 'svelte'

interface Props {
    header: Snippet
    children: Snippet
}

let { header, children }: Props = $props()
</script>

{@render header()}
<main>{@render children()}</main>
'''
        result = component_extractor.extract(code, "Card.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.uses_snippets or comp.uses_runes

    def test_event_dispatcher(self, component_extractor):
        """Test createEventDispatcher extraction."""
        code = '''
<script>
import { createEventDispatcher } from 'svelte'

const dispatch = createEventDispatcher()

function handleClick() {
    dispatch('click', { x: 10, y: 20 })
}
</script>

<button on:click={handleClick}>Click me</button>
'''
        result = component_extractor.extract(code, "Button.svelte")
        components = result.get('components', [])
        assert len(components) >= 1

    def test_module_script(self, component_extractor):
        """Test module context script detection."""
        code = '''
<script context="module">
export const metadata = { title: 'My Component' }
</script>

<script>
export let name
</script>

<p>{name}</p>
'''
        result = component_extractor.extract(code, "WithModule.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.has_module_script

    def test_bindings_extraction(self, component_extractor):
        """Test binding extraction."""
        code = '''
<script>
let value = ''
let inputEl
let group = []
</script>

<input bind:value />
<input bind:this={inputEl} />
<input type="checkbox" bind:group={group} value="a" />
'''
        result = component_extractor.extract(code, "Form.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert len(comp.bindings) >= 1

    def test_transitions_extraction(self, component_extractor):
        """Test transition extraction."""
        code = '''
<script>
import { fade, fly, slide } from 'svelte/transition'
import { flip } from 'svelte/animate'

let visible = true
</script>

{#if visible}
    <div transition:fade={{ duration: 300 }}>Fading</div>
    <div in:fly={{ y: 20 }} out:slide>Flying in, sliding out</div>
{/if}
'''
        result = component_extractor.extract(code, "Animated.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert len(comp.transitions) >= 1

    def test_actions_in_template(self, component_extractor):
        """Test use: action extraction in template."""
        code = '''
<script>
import { clickOutside } from '$lib/actions'
import { tooltip } from '$lib/actions/tooltip'
</script>

<div use:clickOutside={() => open = false}>
    <button use:tooltip={{ text: 'Hello' }}>Hover me</button>
</div>
'''
        result = component_extractor.extract(code, "WithActions.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert len(comp.actions_used) >= 1

    def test_special_elements(self, component_extractor):
        """Test special Svelte elements extraction."""
        code = '''
<script>
let innerWidth

function handleKeydown(e) {
    console.log(e.key)
}
</script>

<svelte:window bind:innerWidth on:keydown={handleKeydown} />
<svelte:head>
    <title>My App</title>
</svelte:head>
<svelte:body on:click={() => console.log('body click')} />
'''
        result = component_extractor.extract(code, "Special.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert len(comp.special_elements) >= 1

    def test_page_component(self, component_extractor):
        """Test SvelteKit page component detection."""
        code = '''
<script lang="ts">
import type { PageData } from './$types'

let { data }: { data: PageData } = $props()
</script>

<h1>{data.title}</h1>
'''
        result = component_extractor.extract(code, "+page.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.is_page

    def test_layout_component(self, component_extractor):
        """Test SvelteKit layout component detection."""
        code = '''
<script>
import Header from '$lib/Header.svelte'
import Footer from '$lib/Footer.svelte'
</script>

<Header />
<main>
    <slot />
</main>
<Footer />
'''
        result = component_extractor.extract(code, "+layout.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.is_layout

    def test_style_lang_detection(self, component_extractor):
        """Test style language detection."""
        code = '''
<script>
let name = 'world'
</script>

<p>{name}</p>

<style lang="scss">
p {
    color: $primary;
    &:hover { color: $secondary; }
}
</style>
'''
        result = component_extractor.extract(code, "Styled.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.has_style
        assert comp.style_lang == "scss"

    def test_bindable_prop_svelte5(self, component_extractor):
        """Test Svelte 5 $bindable prop."""
        code = '''
<script lang="ts">
let { value = $bindable('') }: { value: string } = $props()
</script>

<input bind:value />
'''
        result = component_extractor.extract(code, "Input.svelte")
        components = result.get('components', [])
        assert len(components) >= 1
        comp = components[0]
        assert comp.uses_runes


# ═══════════════════════════════════════════════════════════════════
# Store Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSvelteStoreExtractor:
    """Tests for SvelteStoreExtractor."""

    def test_writable_store(self, store_extractor):
        """Test writable store extraction."""
        code = '''
import { writable } from 'svelte/store'

export const count = writable(0)
export const user = writable<User | null>(null)
'''
        result = store_extractor.extract(code, "stores.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 2
        names = [s.name for s in stores]
        assert 'count' in names
        assert 'user' in names
        count_store = next(s for s in stores if s.name == 'count')
        assert count_store.store_type == 'writable'
        assert count_store.is_exported

    def test_readable_store(self, store_extractor):
        """Test readable store extraction."""
        code = '''
import { readable } from 'svelte/store'

export const time = readable(new Date(), function start(set) {
    const interval = setInterval(() => set(new Date()), 1000)
    return function stop() {
        clearInterval(interval)
    }
})
'''
        result = store_extractor.extract(code, "time.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1
        assert stores[0].store_type == 'readable'

    def test_derived_store(self, store_extractor):
        """Test derived store extraction."""
        code = '''
import { writable, derived } from 'svelte/store'

export const items = writable([])
export const count = derived(items, $items => $items.length)
export const total = derived(items, $items =>
    $items.reduce((sum, item) => sum + item.price, 0)
)
'''
        result = store_extractor.extract(code, "cart.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 3
        derived_stores = [s for s in stores if s.store_type == 'derived']
        assert len(derived_stores) >= 2

    def test_custom_store(self, store_extractor):
        """Test custom store function extraction."""
        code = '''
import { writable } from 'svelte/store'

function createTodoStore() {
    const { subscribe, update } = writable([])
    return {
        subscribe,
        add: (text) => update(todos => [...todos, { text, done: false }]),
        toggle: (id) => update(todos =>
            todos.map(t => t.id === id ? { ...t, done: !t.done } : t)
        ),
    }
}

export const todos = createTodoStore()
'''
        result = store_extractor.extract(code, "todos.ts")
        stores = result.get('stores', [])
        assert len(stores) >= 1

    def test_store_subscriptions(self, store_extractor):
        """Test store subscription detection."""
        code = '''
<script>
import { count, user } from '$lib/stores'

$: doubled = $count * 2
$: greeting = `Hello ${$user?.name ?? 'Guest'}`
</script>

<p>{$count} (doubled: {doubled})</p>
'''
        result = store_extractor.extract(code, "Display.svelte")
        subscriptions = result.get('subscriptions', [])
        assert len(subscriptions) >= 1


# ═══════════════════════════════════════════════════════════════════
# Action Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSvelteActionExtractor:
    """Tests for SvelteActionExtractor."""

    def test_action_with_lifecycle(self, action_extractor):
        """Test action with update and destroy."""
        code = '''
export function clickOutside(node, callback) {
    function handleClick(event) {
        if (!node.contains(event.target)) {
            callback()
        }
    }

    document.addEventListener('click', handleClick, true)

    return {
        destroy() {
            document.removeEventListener('click', handleClick, true)
        }
    }
}
'''
        result = action_extractor.extract(code, "clickOutside.ts")
        actions = result.get('actions', [])
        assert len(actions) >= 1
        action = actions[0]
        assert action.name == 'clickOutside'
        assert action.has_destroy
        assert action.is_exported

    def test_action_with_update(self, action_extractor):
        """Test action with update lifecycle method."""
        code = '''
export function tooltip(node, params) {
    let tip = null

    function show() {
        tip = document.createElement('div')
        tip.textContent = params.text
        document.body.appendChild(tip)
    }

    function hide() {
        tip?.remove()
    }

    node.addEventListener('mouseenter', show)
    node.addEventListener('mouseleave', hide)

    return {
        update(newParams) {
            params = newParams
            if (tip) tip.textContent = newParams.text
        },
        destroy() {
            hide()
            node.removeEventListener('mouseenter', show)
            node.removeEventListener('mouseleave', hide)
        }
    }
}
'''
        result = action_extractor.extract(code, "tooltip.ts")
        actions = result.get('actions', [])
        assert len(actions) >= 1
        action = actions[0]
        assert action.name == 'tooltip'
        assert action.has_update
        assert action.has_destroy

    def test_typed_action(self, action_extractor):
        """Test TypeScript typed action with Action interface."""
        code = '''
import type { Action } from 'svelte/action'

interface TooltipParams {
    text: string
    position?: 'top' | 'bottom'
}

export const tooltip: Action<HTMLElement, TooltipParams> = (node, params) => {
    return {
        update(newParams) {
            params = newParams
        },
        destroy() {
            // cleanup
        }
    }
}
'''
        result = action_extractor.extract(code, "tooltip.ts")
        actions = result.get('actions', [])
        assert len(actions) >= 1


# ═══════════════════════════════════════════════════════════════════
# Routing Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSvelteRoutingExtractor:
    """Tests for SvelteRoutingExtractor."""

    def test_server_load_function(self, routing_extractor):
        """Test server load function extraction."""
        code = '''
import type { PageServerLoad } from './$types'
import { error } from '@sveltejs/kit'
import { db } from '$lib/server/db'

export const load: PageServerLoad = async ({ params }) => {
    const post = await db.post.findUnique({
        where: { slug: params.slug }
    })

    if (!post) throw error(404, 'Post not found')

    return { post }
}
'''
        result = routing_extractor.extract(code, "src/routes/blog/[slug]/+page.server.ts")
        load_fns = result.get('load_functions', [])
        assert len(load_fns) >= 1
        lf = load_fns[0]
        assert lf.is_server

    def test_universal_load_function(self, routing_extractor):
        """Test universal load function extraction."""
        code = '''
import type { PageLoad } from './$types'

export const load: PageLoad = async ({ fetch }) => {
    const res = await fetch('/api/posts')
    const posts = await res.json()
    return { posts }
}
'''
        result = routing_extractor.extract(code, "src/routes/blog/+page.ts")
        load_fns = result.get('load_functions', [])
        assert len(load_fns) >= 1

    def test_form_actions(self, routing_extractor):
        """Test form action extraction."""
        code = '''
import type { Actions } from './$types'
import { fail } from '@sveltejs/kit'

export const actions: Actions = {
    create: async ({ request }) => {
        const data = await request.formData()
        const title = data.get('title')
        if (!title) return fail(400, { title, missing: true })
        await db.todo.create({ data: { title: String(title) } })
        return { success: true }
    },
    delete: async ({ request }) => {
        const data = await request.formData()
        await db.todo.delete({ where: { id: String(data.get('id')) } })
    }
}
'''
        result = routing_extractor.extract(code, "src/routes/todos/+page.server.ts")
        form_actions = result.get('form_actions', [])
        assert len(form_actions) >= 2
        names = [fa.name for fa in form_actions]
        assert 'create' in names
        assert 'delete' in names

    def test_api_endpoint(self, routing_extractor):
        """Test API endpoint extraction."""
        code = '''
import type { RequestHandler } from './$types'
import { json } from '@sveltejs/kit'

export const GET: RequestHandler = async ({ url }) => {
    const limit = Number(url.searchParams.get('limit') ?? '10')
    const users = await db.user.findMany({ take: limit })
    return json(users)
}

export const POST: RequestHandler = async ({ request }) => {
    const data = await request.json()
    const user = await db.user.create({ data })
    return json(user, { status: 201 })
}
'''
        result = routing_extractor.extract(code, "src/routes/api/users/+server.ts")
        routes = result.get('routes', [])
        assert len(routes) >= 1

    def test_hooks_server(self, routing_extractor):
        """Test hooks.server.ts extraction."""
        code = '''
import type { Handle } from '@sveltejs/kit'
import { sequence } from '@sveltejs/kit/hooks'

const auth: Handle = async ({ event, resolve }) => {
    const session = await getSession(event.cookies.get('session'))
    event.locals.user = session?.user ?? null
    return resolve(event)
}

const logger: Handle = async ({ event, resolve }) => {
    const start = performance.now()
    const response = await resolve(event)
    console.log(`${event.request.method} ${event.url.pathname}`)
    return response
}

export const handle = sequence(auth, logger)
'''
        result = routing_extractor.extract(code, "src/hooks.server.ts")
        hooks = result.get('hooks', [])
        assert len(hooks) >= 1

    def test_param_matcher(self, routing_extractor):
        """Test param matcher extraction."""
        code = '''
import type { ParamMatcher } from '@sveltejs/kit'

export const match: ParamMatcher = (param) => {
    return /^\\d+$/.test(param)
}
'''
        result = routing_extractor.extract(code, "src/params/integer.ts")
        matchers = result.get('param_matchers', [])
        assert len(matchers) >= 1

    def test_dynamic_route_detection(self, routing_extractor):
        """Test dynamic route parameter detection from file path."""
        code = '''
<script lang="ts">
import type { PageData } from './$types'
let { data }: { data: PageData } = $props()
</script>

<h1>{data.post.title}</h1>
'''
        result = routing_extractor.extract(code, "src/routes/blog/[slug]/+page.svelte")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        route = routes[0]
        assert route.is_dynamic

    def test_rest_route_detection(self, routing_extractor):
        """Test rest route parameter detection."""
        code = '''
<script lang="ts">
import type { PageData } from './$types'
let { data }: { data: PageData } = $props()
</script>

<p>{data.path}</p>
'''
        result = routing_extractor.extract(code, "src/routes/docs/[...path]/+page.svelte")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        route = routes[0]
        assert route.is_rest


# ═══════════════════════════════════════════════════════════════════
# Lifecycle Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSvelteLifecycleExtractor:
    """Tests for SvelteLifecycleExtractor."""

    def test_lifecycle_hooks(self, lifecycle_extractor):
        """Test lifecycle hook extraction."""
        code = '''
import { onMount, onDestroy, beforeUpdate, afterUpdate } from 'svelte'

onMount(() => {
    console.log('mounted')
    return () => console.log('cleanup')
})

onDestroy(() => {
    console.log('destroyed')
})

beforeUpdate(() => {
    console.log('before update')
})

afterUpdate(() => {
    console.log('after update')
})
'''
        result = lifecycle_extractor.extract(code, "Component.svelte")
        hooks = result.get('lifecycle_hooks', [])
        assert len(hooks) >= 4
        hook_names = [h.name for h in hooks]
        assert 'onMount' in hook_names
        assert 'onDestroy' in hook_names

    def test_context_api(self, lifecycle_extractor):
        """Test context API extraction."""
        code = '''
import { setContext, getContext } from 'svelte'
import { writable } from 'svelte/store'

setContext('theme', writable('light'))

// In child component:
const theme = getContext('theme')
'''
        result = lifecycle_extractor.extract(code, "Theme.svelte")
        contexts = result.get('contexts', [])
        assert len(contexts) >= 1

    def test_svelte5_runes_extraction(self, lifecycle_extractor):
        """Test Svelte 5 rune extraction."""
        code = '''
let count = $state(0)
let doubled = $derived(count * 2)
let items = $state.raw([])

$effect(() => {
    console.log(count)
    return () => console.log('cleanup')
})

$effect.pre(() => {
    console.log('before update')
})

$inspect(count, doubled)
'''
        result = lifecycle_extractor.extract(code, "Runes.svelte")
        runes = result.get('runes', [])
        assert len(runes) >= 3  # $state, $derived, $effect, etc.
        rune_names = [r.name for r in runes]
        assert any('state' in n or '$state' in n for n in rune_names)

    def test_async_onmount(self, lifecycle_extractor):
        """Test async onMount detection."""
        code = '''
import { onMount } from 'svelte'

onMount(async () => {
    const data = await fetch('/api/data')
    items = await data.json()
})
'''
        result = lifecycle_extractor.extract(code, "Async.svelte")
        hooks = result.get('lifecycle_hooks', [])
        assert len(hooks) >= 1
        assert hooks[0].name == 'onMount'
        assert hooks[0].is_async


# ═══════════════════════════════════════════════════════════════════
# Enhanced Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedSvelteParser:
    """Tests for the integrated EnhancedSvelteParser."""

    def test_parser_initialization(self, parser):
        """Test that parser initializes all extractors."""
        assert parser.component_extractor is not None
        assert parser.store_extractor is not None
        assert parser.action_extractor is not None
        assert parser.routing_extractor is not None
        assert parser.lifecycle_extractor is not None

    def test_parse_svelte_component(self, parser):
        """Test full parsing of a Svelte 5 component."""
        code = '''
<script lang="ts">
import { writable } from 'svelte/store'

let count = $state(0)
let doubled = $derived(count * 2)

const name = writable('World')

$effect(() => {
    console.log('count changed:', count)
})

interface Props {
    title: string
}
let { title }: Props = $props()
</script>

<h1>{title}</h1>
<p>Count: {count}, Doubled: {doubled}</p>
<p>Hello {$name}!</p>

<style lang="scss">
h1 { color: red; }
</style>
'''
        result = parser.parse(code, "App.svelte")
        assert isinstance(result, SvelteParseResult)
        assert result.file_path == "App.svelte"
        assert result.file_type == "svelte"
        assert result.uses_runes
        assert result.uses_typescript
        assert result.svelte_version == '5.0'

    def test_parse_sveltekit_page_server(self, parser):
        """Test parsing of +page.server.ts."""
        code = '''
import type { PageServerLoad, Actions } from './$types'
import { error, fail } from '@sveltejs/kit'
import { db } from '$lib/server/db'

export const load: PageServerLoad = async ({ params }) => {
    const post = await db.post.findUnique({
        where: { slug: params.slug }
    })
    if (!post) throw error(404, 'Not found')
    return { post }
}

export const actions: Actions = {
    update: async ({ request }) => {
        const data = await request.formData()
        const title = data.get('title')
        if (!title) return fail(400, { missing: true })
        await db.post.update({ where: { slug: data.get('slug') }, data: { title } })
    }
}
'''
        result = parser.parse(code, "src/routes/blog/[slug]/+page.server.ts")
        assert result.file_type == "ts"
        assert result.uses_typescript
        assert len(result.load_functions) >= 1
        assert len(result.form_actions) >= 1
        assert result.sveltekit_version >= '1.0'

    def test_parse_svelte_module_ts(self, parser):
        """Test parsing of .svelte.ts module file."""
        code = '''
let count = $state(0)
let doubled = $derived(count * 2)

export function increment() {
    count++
}

export function getCount() {
    return count
}
'''
        result = parser.parse(code, "lib/state/counter.svelte.ts")
        assert result.file_type == "svelte.ts"
        assert result.uses_runes
        assert len(result.runes) >= 2

    def test_framework_detection_skeleton_ui(self, parser):
        """Test Skeleton UI framework detection."""
        code = '''
<script>
import { AppShell, AppBar, TabGroup, Tab } from '@skeletonlabs/skeleton'
</script>

<AppShell>
    <svelte:fragment slot="header">
        <AppBar />
    </svelte:fragment>
    <slot />
</AppShell>
'''
        result = parser.parse(code, "Layout.svelte")
        assert 'skeleton-ui' in result.detected_frameworks

    def test_framework_detection_shadcn_svelte(self, parser):
        """Test shadcn-svelte detection."""
        code = '''
<script>
import { Button } from '$lib/components/ui/button'
import { Card } from '$lib/components/ui/card'
</script>

<Card.Root>
    <Card.Content>
        <Button>Click me</Button>
    </Card.Content>
</Card.Root>
'''
        result = parser.parse(code, "Page.svelte")
        assert 'shadcn-svelte' in result.detected_frameworks

    def test_framework_detection_superforms(self, parser):
        """Test Superforms detection."""
        code = '''
<script>
import { superForm } from 'sveltekit-superforms/client'
import SuperDebug from 'sveltekit-superforms/client/SuperDebug.svelte'

const { form, errors, enhance } = superForm(data.form)
</script>

<form method="POST" use:enhance>
    <input name="email" bind:value={$form.email} />
    {#if $errors.email}
        <p class="error">{$errors.email}</p>
    {/if}
</form>
'''
        result = parser.parse(code, "Login.svelte")
        assert 'superforms' in result.detected_frameworks

    def test_framework_detection_tailwind(self, parser):
        """Test Tailwind CSS detection."""
        code = '''
<div class="flex items-center justify-between p-4 bg-white rounded-lg shadow">
    <h1 class="text-2xl font-bold text-gray-900">Title</h1>
    <button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        Click me
    </button>
</div>
'''
        result = parser.parse(code, "Card.svelte")
        assert 'tailwindcss' in result.detected_frameworks

    def test_framework_detection_houdini(self, parser):
        """Test Houdini GraphQL detection."""
        code = '''
<script>
import { graphql } from '$houdini'

const AllUsers = graphql(`
    query AllUsers {
        users {
            id
            name
            email
        }
    }
`)
</script>
'''
        result = parser.parse(code, "Users.svelte")
        assert 'houdini' in result.detected_frameworks

    def test_framework_detection_lucia_auth(self, parser):
        """Test Lucia auth detection."""
        code = '''
import { Lucia } from 'lucia'
import { dev } from '$app/environment'

export const lucia = new Lucia(adapter, {
    sessionCookie: { attributes: { secure: !dev } }
})
'''
        result = parser.parse(code, "auth.ts")
        assert 'lucia' in result.detected_frameworks

    def test_svelte_version_detection_v3(self, parser):
        """Test Svelte 3 version detection."""
        code = '''
<script>
import { createEventDispatcher } from 'svelte'

export let name = 'world'

const dispatch = createEventDispatcher()

$: greeting = `Hello ${name}!`
</script>

<p>{greeting}</p>
'''
        result = parser.parse(code, "Hello.svelte")
        assert result.svelte_version == '3.0'
        assert not result.uses_runes

    def test_svelte_version_detection_v5(self, parser):
        """Test Svelte 5 version detection."""
        code = '''
<script lang="ts">
let name = $state('world')
let greeting = $derived(`Hello ${name}!`)

$effect(() => {
    document.title = greeting
})
</script>

<input bind:value={name} />
<p>{greeting}</p>
'''
        result = parser.parse(code, "Hello.svelte")
        assert result.svelte_version == '5.0'
        assert result.uses_runes

    def test_sveltekit_version_detection_v1(self, parser):
        """Test SvelteKit 1 detection."""
        code = '''
import type { PageServerLoad } from './$types'

export const load: PageServerLoad = async ({ params }) => {
    return { slug: params.slug }
}
'''
        result = parser.parse(code, "src/routes/[slug]/+page.server.ts")
        assert result.sveltekit_version >= '1.0'

    def test_sveltekit_version_detection_v2(self, parser):
        """Test SvelteKit 2 detection."""
        code = '''
import { pushState, replaceState } from '$app/navigation'

function handleShallowNavigation() {
    pushState('/modal', { showModal: true })
}
'''
        result = parser.parse(code, "Page.svelte")
        assert result.sveltekit_version == '2.0'

    def test_is_svelte_file_svelte(self, parser):
        """Test .svelte file detection."""
        assert parser.is_svelte_file("", "Component.svelte")
        assert parser.is_svelte_file("", "+page.svelte")
        assert parser.is_svelte_file("", "+layout.svelte")

    def test_is_svelte_file_svelte_ts(self, parser):
        """Test .svelte.ts file detection."""
        assert parser.is_svelte_file("", "counter.svelte.ts")
        assert parser.is_svelte_file("", "state.svelte.js")

    def test_is_svelte_file_sveltekit_routing(self, parser):
        """Test SvelteKit routing file detection."""
        assert parser.is_svelte_file("", "+page.ts")
        assert parser.is_svelte_file("", "+page.server.ts")
        assert parser.is_svelte_file("", "+server.ts")
        assert parser.is_svelte_file("", "+layout.ts")
        assert parser.is_svelte_file("", "+layout.server.ts")
        assert parser.is_svelte_file("", "hooks.server.ts")
        assert parser.is_svelte_file("", "hooks.client.ts")

    def test_is_svelte_file_with_imports(self, parser):
        """Test detection via Svelte imports in JS/TS."""
        code = "import { writable } from 'svelte/store'"
        assert parser.is_svelte_file(code, "stores.ts")

    def test_is_svelte_file_with_runes(self, parser):
        """Test detection via runes in TS."""
        code = "let count = $state(0)"
        assert parser.is_svelte_file(code, "counter.ts")

    def test_is_not_svelte_file(self, parser):
        """Test non-Svelte file rejection."""
        code = "const x = 5\nconsole.log(x)"
        assert not parser.is_svelte_file(code, "util.js")

    def test_rendering_config_detection(self, parser):
        """Test SSR/CSR/prerender configuration detection."""
        code = '''
export const prerender = true
export const ssr = false
export const csr = true
'''
        result = parser.parse(code, "+page.ts")
        assert result.has_prerender
        assert result.has_ssr
        assert result.has_csr

    def test_full_component_with_all_features(self, parser):
        """Test comprehensive component with many features."""
        code = '''
<script context="module">
export const prerender = true
</script>

<script lang="ts">
import { onMount, setContext } from 'svelte'
import { writable } from 'svelte/store'
import { fade, fly } from 'svelte/transition'
import { flip } from 'svelte/animate'
import { clickOutside } from '$lib/actions'
import Button from '$lib/components/Button.svelte'

export let items = []
export let title = 'My List'

const count = writable(0)

let inputValue = ''
let inputEl

onMount(() => {
    inputEl.focus()
    return () => console.log('cleanup')
})

setContext('list', { items, count })

$: filteredItems = items.filter(item => item.active)
$: total = filteredItems.length

function addItem() {
    items = [...items, { text: inputValue, active: true }]
    inputValue = ''
}
</script>

<svelte:head>
    <title>{title}</title>
</svelte:head>

<svelte:window on:keydown={handleKey} />

<div use:clickOutside={() => open = false}>
    <h1>{title} ({total})</h1>

    <input
        bind:this={inputEl}
        bind:value={inputValue}
        on:keydown|preventDefault={handleKey}
    />
    <Button on:click={addItem}>Add</Button>

    {#each filteredItems as item (item.id)}
        <div
            animate:flip={{ duration: 300 }}
            in:fly={{ y: 20, duration: 200 }}
            out:fade={{ duration: 150 }}
        >
            {item.text}
        </div>
    {/each}

    <slot name="footer" {total} />
</div>

<style lang="scss">
h1 {
    color: $primary;
    &:hover { text-decoration: underline; }
}
</style>
'''
        result = parser.parse(code, "TodoList.svelte")
        assert result.file_type == "svelte"
        assert result.uses_typescript
        assert result.svelte_version == '3.0'
        assert len(result.components) >= 1
        assert len(result.stores) >= 1
        assert len(result.lifecycle_hooks) >= 1
        assert len(result.contexts) >= 1

    def test_parse_empty_file(self, parser):
        """Test parsing an empty file."""
        result = parser.parse("", "Empty.svelte")
        assert isinstance(result, SvelteParseResult)
        assert result.file_path == "Empty.svelte"
        assert result.file_type == "svelte"

    def test_parse_minimal_component(self, parser):
        """Test parsing a minimal Svelte component."""
        code = "<p>Hello World</p>"
        result = parser.parse(code, "Hello.svelte")
        assert isinstance(result, SvelteParseResult)
        assert result.file_type == "svelte"

    def test_multiple_framework_detection(self, parser):
        """Test detection of multiple frameworks."""
        code = '''
<script lang="ts">
import { AppShell } from '@skeletonlabs/skeleton'
import { superForm } from 'sveltekit-superforms/client'
import { createQuery } from '@tanstack/svelte-query'
import { z } from 'zod'
import { onMount } from 'svelte'
</script>
'''
        result = parser.parse(code, "Complex.svelte")
        assert 'skeleton-ui' in result.detected_frameworks
        assert 'superforms' in result.detected_frameworks
        assert 'tanstack-query-svelte' in result.detected_frameworks
        assert 'zod' in result.detected_frameworks
        assert 'svelte' in result.detected_frameworks

    def test_version_compare_utility(self, parser):
        """Test version comparison utility."""
        assert EnhancedSvelteParser._version_compare('5.0', '3.0') > 0
        assert EnhancedSvelteParser._version_compare('3.0', '5.0') < 0
        assert EnhancedSvelteParser._version_compare('4.0', '4.0') == 0
        assert EnhancedSvelteParser._version_compare('5.1', '5.0') > 0


# ═══════════════════════════════════════════════════════════════════
# BPL Practices Tests
# ═══════════════════════════════════════════════════════════════════

class TestSvelteBPLPractices:
    """Tests for Svelte BPL practices YAML."""

    def test_practices_file_loads(self):
        """Test that svelte_core.yaml loads correctly."""
        import yaml
        import os

        practices_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'codetrellis', 'bpl', 'practices', 'svelte_core.yaml'
        )
        assert os.path.exists(practices_path), f"svelte_core.yaml not found at {practices_path}"

        with open(practices_path, 'r') as f:
            data = yaml.safe_load(f)

        assert data is not None
        assert 'practices' in data
        assert data['framework'] == 'svelte'

    def test_practices_count(self):
        """Test that exactly 50 practices are defined."""
        import yaml
        import os

        practices_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'codetrellis', 'bpl', 'practices', 'svelte_core.yaml'
        )
        with open(practices_path, 'r') as f:
            data = yaml.safe_load(f)

        practices = data['practices']
        assert len(practices) == 50, f"Expected 50 practices, got {len(practices)}"

    def test_practices_ids_unique(self):
        """Test that all practice IDs are unique."""
        import yaml
        import os

        practices_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'codetrellis', 'bpl', 'practices', 'svelte_core.yaml'
        )
        with open(practices_path, 'r') as f:
            data = yaml.safe_load(f)

        ids = [p['id'] for p in data['practices']]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {[id for id in ids if ids.count(id) > 1]}"

    def test_practices_ids_sequential(self):
        """Test that practice IDs are SVELTE001-SVELTE050."""
        import yaml
        import os

        practices_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'codetrellis', 'bpl', 'practices', 'svelte_core.yaml'
        )
        with open(practices_path, 'r') as f:
            data = yaml.safe_load(f)

        ids = [p['id'] for p in data['practices']]
        for i, pid in enumerate(ids, 1):
            expected = f"SVELTE{i:03d}"
            assert pid == expected, f"Expected {expected}, got {pid} at position {i}"

    def test_practices_have_required_fields(self):
        """Test that all practices have required fields."""
        import yaml
        import os

        practices_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'codetrellis', 'bpl', 'practices', 'svelte_core.yaml'
        )
        with open(practices_path, 'r') as f:
            data = yaml.safe_load(f)

        required_fields = ['id', 'title', 'category', 'level', 'priority', 'content', 'tags']
        for practice in data['practices']:
            for field in required_fields:
                assert field in practice, f"Practice {practice.get('id', '?')} missing field: {field}"

    def test_practices_categories_valid(self):
        """Test that all practice categories are valid PracticeCategory values."""
        import yaml
        import os
        from codetrellis.bpl.models import PracticeCategory

        practices_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'codetrellis', 'bpl', 'practices', 'svelte_core.yaml'
        )
        with open(practices_path, 'r') as f:
            data = yaml.safe_load(f)

        valid_categories = {e.value for e in PracticeCategory}
        for practice in data['practices']:
            cat = practice['category']
            assert cat in valid_categories, (
                f"Practice {practice['id']} has invalid category: {cat}. "
                f"Valid Svelte categories: {[v for v in valid_categories if 'svelte' in v]}"
            )


# ═══════════════════════════════════════════════════════════════════
# Integration / Edge Cases
# ═══════════════════════════════════════════════════════════════════

class TestSvelteEdgeCases:
    """Tests for edge cases and error handling."""

    def test_malformed_svelte_file(self, parser):
        """Test parsing a malformed Svelte file."""
        code = '''
<script>
let x = {
  // unterminated object
</script>

<div>
  <!-- unclosed div
'''
        result = parser.parse(code, "Broken.svelte")
        assert isinstance(result, SvelteParseResult)

    def test_very_large_component(self, parser):
        """Test parsing a very large component doesn't crash."""
        # Generate a large component
        props = "\n".join([f"export let prop{i} = {i}" for i in range(100)])
        code = f"<script>\n{props}\n</script>\n<p>Large component</p>"
        result = parser.parse(code, "Large.svelte")
        assert isinstance(result, SvelteParseResult)

    def test_unicode_content(self, parser):
        """Test parsing component with unicode content."""
        code = '''
<script>
let name = '世界'
let emoji = '🎉'
</script>

<p>こんにちは {name} {emoji}</p>
'''
        result = parser.parse(code, "Unicode.svelte")
        assert isinstance(result, SvelteParseResult)

    def test_mixed_svelte_versions(self, parser):
        """Test component mixing Svelte 3 and 5 syntax."""
        code = '''
<script>
import { createEventDispatcher } from 'svelte'

// Svelte 3/4 style
export let name = 'world'
const dispatch = createEventDispatcher()

// Svelte 5 style
let count = $state(0)
let doubled = $derived(count * 2)
</script>

<p>{name}: {count}</p>
'''
        result = parser.parse(code, "Mixed.svelte")
        assert result.svelte_version == '5.0'
        assert result.uses_runes

    def test_no_script_tag(self, parser):
        """Test component with no script tag."""
        code = '''
<h1>Static Content</h1>
<p>No script needed</p>

<style>
h1 { color: blue; }
</style>
'''
        result = parser.parse(code, "Static.svelte")
        assert isinstance(result, SvelteParseResult)
        assert result.file_type == "svelte"
