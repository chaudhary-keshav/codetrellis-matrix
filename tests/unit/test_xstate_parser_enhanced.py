"""
Tests for XState extractors and EnhancedXstateParser.

Part of CodeTrellis v4.55 XState State Machine Framework Support.
Tests cover:
- Machine extraction (createMachine, Machine, setup, versions v3-v5)
- State extraction (atomic, compound, parallel, final, history, transitions, invokes)
- Action extraction (assign, send, raise, log, stop, enqueueActions, emit, sendTo)
- Guard extraction (cond, guard, not, and, or, stateIn, inline)
- API extraction (imports, createActor, interpret, useMachine, fromPromise, typegens)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.xstate_parser_enhanced import (
    EnhancedXstateParser,
    XstateParseResult,
)
from codetrellis.extractors.xstate import (
    XstateMachineExtractor,
    XstateMachineInfo,
    XstateStateExtractor,
    XstateStateNodeInfo,
    XstateTransitionInfo,
    XstateInvokeInfo,
    XstateActionExtractor,
    XstateActionInfo,
    XstateGuardExtractor,
    XstateGuardInfo,
    XstateApiExtractor,
    XstateImportInfo,
    XstateActorInfo,
    XstateTypegenInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedXstateParser()


@pytest.fixture
def machine_extractor():
    return XstateMachineExtractor()


@pytest.fixture
def state_extractor():
    return XstateStateExtractor()


@pytest.fixture
def action_extractor():
    return XstateActionExtractor()


@pytest.fixture
def guard_extractor():
    return XstateGuardExtractor()


@pytest.fixture
def api_extractor():
    return XstateApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Machine Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestXstateMachineExtractor:
    """Tests for XstateMachineExtractor."""

    def test_basic_create_machine(self, machine_extractor):
        code = '''
import { createMachine } from 'xstate';

const toggleMachine = createMachine({
    id: 'toggle',
    initial: 'inactive',
    states: {
        inactive: { on: { TOGGLE: 'active' } },
        active: { on: { TOGGLE: 'inactive' } },
    },
});
'''
        result = machine_extractor.extract(code, "toggle.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        machine = machines[0]
        assert machine.name == "toggleMachine"
        assert machine.creation_method == "createMachine"
        assert machine.machine_id == "toggle"
        assert machine.initial_state == "inactive"

    def test_machine_with_context(self, machine_extractor):
        code = '''
const counterMachine = createMachine({
    id: 'counter',
    initial: 'active',
    context: { count: 0, max: 100 },
    states: {
        active: {
            on: {
                INC: { actions: 'increment' },
                DEC: { actions: 'decrement' },
            },
        },
    },
});
'''
        result = machine_extractor.extract(code, "counter.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        assert machines[0].has_context is True

    def test_v3_machine_function(self, machine_extractor):
        code = '''
import { Machine } from 'xstate';

const lightMachine = Machine({
    id: 'light',
    initial: 'green',
    states: {
        green: { on: { TIMER: 'yellow' } },
        yellow: { on: { TIMER: 'red' } },
        red: { on: { TIMER: 'green' } },
    },
});
'''
        result = machine_extractor.extract(code, "light.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        assert machines[0].creation_method == "Machine"
        assert machines[0].machine_id == "light"

    def test_v5_setup_machine(self, machine_extractor):
        code = '''
import { setup, assign } from 'xstate';

const fetchMachine = setup({
    types: {} as {
        context: { data: string | null; error: string | null };
        events: { type: 'FETCH' } | { type: 'RETRY' };
    },
    actions: {
        clearError: assign({ error: null }),
        setData: assign({ data: ({ event }) => event.output }),
    },
    guards: {
        hasData: ({ context }) => context.data !== null,
    },
    actors: {
        fetchData: fromPromise(async () => { return 'data'; }),
    },
}).createMachine({
    id: 'fetch',
    initial: 'idle',
    context: { data: null, error: null },
    states: {
        idle: { on: { FETCH: 'loading' } },
        loading: { on: { SUCCESS: 'success' } },
        success: { type: 'final' },
    },
});
'''
        result = machine_extractor.extract(code, "fetch.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        machine = machines[0]
        assert machine.creation_method == "setup"
        assert machine.has_setup is True

    def test_exported_machine(self, machine_extractor):
        code = '''
export const authMachine = createMachine({
    id: 'auth',
    initial: 'idle',
    states: {
        idle: {},
        authenticating: {},
        authenticated: {},
    },
});
'''
        result = machine_extractor.extract(code, "auth.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        assert machines[0].is_exported is True

    def test_machine_with_parallel_states(self, machine_extractor):
        code = '''
const dashMachine = createMachine({
    id: 'dashboard',
    type: 'parallel',
    states: {
        sidebar: { initial: 'open', states: { open: {}, closed: {} } },
        main: { initial: 'list', states: { list: {}, detail: {} } },
    },
});
'''
        result = machine_extractor.extract(code, "dash.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        assert machines[0].has_parallel is True

    def test_machine_with_invoke(self, machine_extractor):
        code = '''
const dataMachine = createMachine({
    id: 'data',
    initial: 'loading',
    states: {
        loading: {
            invoke: {
                src: 'fetchData',
                onDone: 'success',
                onError: 'error',
            },
        },
        success: { type: 'final' },
        error: {},
    },
});
'''
        result = machine_extractor.extract(code, "data.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        assert machines[0].has_invoke is True
        assert machines[0].has_final is True

    def test_machine_with_after_always(self, machine_extractor):
        code = '''
const timerMachine = createMachine({
    id: 'timer',
    initial: 'idle',
    states: {
        idle: { on: { START: 'running' } },
        running: {
            after: { 1000: 'done' },
        },
        checking: {
            always: [
                { guard: 'isValid', target: 'valid' },
                { target: 'invalid' },
            ],
        },
        valid: {},
        invalid: {},
        done: { type: 'final' },
    },
});
'''
        result = machine_extractor.extract(code, "timer.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        assert machines[0].has_after is True
        assert machines[0].has_always is True

    def test_machine_with_tsTypes(self, machine_extractor):
        code = '''
const formMachine = createMachine({
    tsTypes: {} as import('./form.machine.typegen').Typegen0,
    schema: {
        context: {} as FormContext,
        events: {} as FormEvent,
    },
    id: 'form',
    initial: 'editing',
    states: { editing: {}, submitted: {} },
});
'''
        result = machine_extractor.extract(code, "form.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        assert machines[0].has_tsTypes is True

    def test_multiple_machines_in_file(self, machine_extractor):
        code = '''
const machine1 = createMachine({
    id: 'first',
    initial: 'idle',
    states: { idle: {} },
});

const machine2 = createMachine({
    id: 'second',
    initial: 'ready',
    states: { ready: {} },
});
'''
        result = machine_extractor.extract(code, "multi.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 2

    def test_setup_with_actions_guards_actors(self, machine_extractor):
        code = '''
const machine = setup({
    actions: {
        increment: assign({ count: ({ context }) => context.count + 1 }),
        logEvent: ({ context, event }) => console.log(event),
    },
    guards: {
        isPositive: ({ context }) => context.count > 0,
        isMax: ({ context }) => context.count >= 100,
    },
    actors: {
        fetchUser: fromPromise(async ({ input }) => fetch(input.url)),
    },
}).createMachine({
    id: 'counter',
    initial: 'active',
    context: { count: 0 },
    states: { active: {} },
});
'''
        result = machine_extractor.extract(code, "setup.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        machine = machines[0]
        assert machine.has_setup is True
        assert len(machine.setup_actions) >= 1
        assert len(machine.setup_guards) >= 1
        assert len(machine.setup_actors) >= 1

    def test_predictable_action_args(self, machine_extractor):
        code = '''
const machine = createMachine({
    id: 'compat',
    predictableActionArguments: true,
    initial: 'idle',
    context: { value: 0 },
    states: { idle: {} },
});
'''
        result = machine_extractor.extract(code, "compat.ts")
        machines = result.get('machines', [])
        assert len(machines) >= 1
        assert machines[0].predictable_action_args is True


# ═══════════════════════════════════════════════════════════════════
# State Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestXstateStateExtractor:
    """Tests for XstateStateExtractor."""

    def test_basic_state_nodes(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'test',
    initial: 'idle',
    states: {
        idle: { on: { START: 'loading' } },
        loading: {},
        success: {},
        error: {},
    },
});
'''
        result = state_extractor.extract(code, "states.ts")
        state_nodes = result.get('state_nodes', [])
        assert len(state_nodes) >= 2
        names = [sn.name for sn in state_nodes]
        assert 'idle' in names

    def test_entry_exit_actions(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'lifecycle',
    initial: 'active',
    states: {
        active: {
            entry: ['startTimer', 'logEntry'],
            exit: ['stopTimer'],
            on: { STOP: 'idle' },
        },
        idle: {},
    },
});
'''
        result = state_extractor.extract(code, "lifecycle.ts")
        state_nodes = result.get('state_nodes', [])
        active_nodes = [sn for sn in state_nodes if sn.name == 'active']
        assert len(active_nodes) >= 1
        assert active_nodes[0].has_entry is True
        assert active_nodes[0].has_exit is True

    def test_parallel_state_type(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'parallel',
    type: 'parallel',
    states: {
        upload: { initial: 'idle', states: { idle: {}, uploading: {} } },
        validation: { initial: 'idle', states: { idle: {}, validating: {} } },
    },
});
'''
        result = state_extractor.extract(code, "parallel.ts")
        state_nodes = result.get('state_nodes', [])
        assert len(state_nodes) >= 1

    def test_final_state_type(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'workflow',
    initial: 'working',
    states: {
        working: { on: { DONE: 'complete' } },
        complete: { type: 'final' },
    },
});
'''
        result = state_extractor.extract(code, "final.ts")
        state_nodes = result.get('state_nodes', [])
        final_nodes = [sn for sn in state_nodes if sn.state_type == 'final']
        assert len(final_nodes) >= 1

    def test_transitions(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'nav',
    initial: 'home',
    states: {
        home: { on: { GO_ABOUT: 'about', GO_CONTACT: 'contact' } },
        about: { on: { GO_HOME: 'home' } },
        contact: { on: { GO_HOME: 'home' } },
    },
});
'''
        result = state_extractor.extract(code, "nav.ts")
        transitions = result.get('transitions', [])
        assert len(transitions) >= 2

    def test_guarded_transitions(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'form',
    initial: 'editing',
    states: {
        editing: {
            on: {
                SUBMIT: [
                    { guard: 'isValid', target: 'submitting' },
                    { target: 'error' },
                ],
            },
        },
        submitting: {},
        error: {},
    },
});
'''
        result = state_extractor.extract(code, "form.ts")
        transitions = result.get('transitions', [])
        guarded = [t for t in transitions if t.has_guard]
        assert len(guarded) >= 1

    def test_invoke_extraction(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'data',
    initial: 'loading',
    states: {
        loading: {
            invoke: {
                id: 'fetchService',
                src: 'fetchData',
                onDone: { target: 'success', actions: 'setData' },
                onError: { target: 'error', actions: 'setError' },
            },
        },
        success: {},
        error: {},
    },
});
'''
        result = state_extractor.extract(code, "invoke.ts")
        invokes = result.get('invokes', [])
        assert len(invokes) >= 1
        assert invokes[0].has_on_done is True
        assert invokes[0].has_on_error is True

    def test_state_with_tags(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'tagged',
    initial: 'loading',
    states: {
        loading: {
            tags: ['busy', 'loading'],
            on: { DONE: 'idle' },
        },
        idle: { tags: ['ready'] },
    },
});
'''
        result = state_extractor.extract(code, "tagged.ts")
        state_nodes = result.get('state_nodes', [])
        tagged = [sn for sn in state_nodes if sn.tags]
        assert len(tagged) >= 1

    def test_history_state(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'wizard',
    initial: 'step1',
    states: {
        step1: { on: { NEXT: 'step2' } },
        step2: { on: { NEXT: 'step3', BACK: 'step1' } },
        step3: { on: { BACK: 'step2' } },
        hist: { type: 'history', history: 'shallow' },
    },
});
'''
        result = state_extractor.extract(code, "wizard.ts")
        state_nodes = result.get('state_nodes', [])
        hist_nodes = [sn for sn in state_nodes if sn.state_type == 'history']
        assert len(hist_nodes) >= 1

    def test_always_transitions(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'router',
    initial: 'checking',
    states: {
        checking: {
            always: [
                { guard: 'isAdmin', target: 'admin' },
                { guard: 'isUser', target: 'user' },
                { target: 'guest' },
            ],
        },
        admin: {},
        user: {},
        guest: {},
    },
});
'''
        result = state_extractor.extract(code, "router.ts")
        state_nodes = result.get('state_nodes', [])
        checking = [sn for sn in state_nodes if sn.name == 'checking']
        assert len(checking) >= 1
        assert checking[0].has_always is True

    def test_after_delayed_transitions(self, state_extractor):
        code = '''
const machine = createMachine({
    id: 'debounce',
    initial: 'idle',
    states: {
        idle: { on: { INPUT: 'debouncing' } },
        debouncing: {
            after: { 300: 'searching' },
            on: { INPUT: 'debouncing' },
        },
        searching: {},
    },
});
'''
        result = state_extractor.extract(code, "debounce.ts")
        state_nodes = result.get('state_nodes', [])
        debouncing = [sn for sn in state_nodes if sn.name == 'debouncing']
        assert len(debouncing) >= 1
        assert debouncing[0].has_after is True


# ═══════════════════════════════════════════════════════════════════
# Action Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestXstateActionExtractor:
    """Tests for XstateActionExtractor."""

    def test_assign_action(self, action_extractor):
        code = '''
import { assign } from 'xstate';

const increment = assign({
    count: ({ context }) => context.count + 1,
});

const setUser = assign({
    user: ({ event }) => event.data,
    loading: false,
});
'''
        result = action_extractor.extract(code, "actions.ts")
        actions = result.get('actions', [])
        assigns = [a for a in actions if a.action_type == 'assign']
        assert len(assigns) >= 1

    def test_send_action(self, action_extractor):
        code = '''
import { send } from 'xstate';

const notifyParent = send({ type: 'CHILD_DONE' }, { to: 'parent' });
const triggerFetch = send('FETCH');
'''
        result = action_extractor.extract(code, "send.ts")
        actions = result.get('actions', [])
        sends = [a for a in actions if a.action_type == 'send']
        assert len(sends) >= 1

    def test_raise_action(self, action_extractor):
        code = '''
import { raise } from 'xstate';

const raiseValidate = raise({ type: 'VALIDATE' });
'''
        result = action_extractor.extract(code, "raise.ts")
        actions = result.get('actions', [])
        raises = [a for a in actions if a.action_type == 'raise']
        assert len(raises) >= 1

    def test_log_action(self, action_extractor):
        code = '''
import { log } from 'xstate';

const logContext = log(({ context }) => `Count is ${context.count}`);
'''
        result = action_extractor.extract(code, "log.ts")
        actions = result.get('actions', [])
        logs = [a for a in actions if a.action_type == 'log']
        assert len(logs) >= 1

    def test_stop_action(self, action_extractor):
        code = '''
import { stop } from 'xstate';

const stopChild = stop('childActor');
'''
        result = action_extractor.extract(code, "stop.ts")
        actions = result.get('actions', [])
        stops = [a for a in actions if a.action_type == 'stop']
        assert len(stops) >= 1

    def test_enqueue_actions_v5(self, action_extractor):
        code = '''
import { enqueueActions } from 'xstate';

const handleResult = enqueueActions(({ enqueue, context }) => {
    enqueue.assign({ processed: true });
    if (context.shouldNotify) {
        enqueue({ type: 'sendNotification' });
    }
});
'''
        result = action_extractor.extract(code, "enqueue.ts")
        actions = result.get('actions', [])
        enqueues = [a for a in actions if a.action_type == 'enqueueActions']
        assert len(enqueues) >= 1

    def test_emit_action_v5(self, action_extractor):
        code = '''
import { emit } from 'xstate';

const notifyDone = emit({ type: 'notification', message: 'Complete!' });
'''
        result = action_extractor.extract(code, "emit.ts")
        actions = result.get('actions', [])
        emits = [a for a in actions if a.action_type == 'emit']
        assert len(emits) >= 1

    def test_choose_action(self, action_extractor):
        code = '''
import { choose } from 'xstate';

const conditionalAction = choose([
    { cond: 'isValid', actions: ['save', 'notify'] },
    { actions: ['showError'] },
]);
'''
        result = action_extractor.extract(code, "choose.ts")
        actions = result.get('actions', [])
        chooses = [a for a in actions if a.action_type == 'choose']
        assert len(chooses) >= 1

    def test_pure_action(self, action_extractor):
        code = '''
import { pure } from 'xstate';

const dynamicAction = pure((context, event) => {
    return context.isActive ? [assign({ count: context.count + 1 })] : [];
});
'''
        result = action_extractor.extract(code, "pure.ts")
        actions = result.get('actions', [])
        pures = [a for a in actions if a.action_type == 'pure']
        assert len(pures) >= 1

    def test_forward_to_action(self, action_extractor):
        code = '''
import { forwardTo } from 'xstate';

const fwd = forwardTo('childActor');
'''
        result = action_extractor.extract(code, "forward.ts")
        actions = result.get('actions', [])
        forwards = [a for a in actions if a.action_type == 'forwardTo']
        assert len(forwards) >= 1

    def test_escalate_action(self, action_extractor):
        code = '''
import { escalate } from 'xstate';

const escalateError = escalate({ message: 'Something went wrong' });
'''
        result = action_extractor.extract(code, "escalate.ts")
        actions = result.get('actions', [])
        escalates = [a for a in actions if a.action_type == 'escalate']
        assert len(escalates) >= 1

    def test_respond_action(self, action_extractor):
        code = '''
import { respond } from 'xstate';

const respondOk = respond({ type: 'OK' });
'''
        result = action_extractor.extract(code, "respond.ts")
        actions = result.get('actions', [])
        responds = [a for a in actions if a.action_type == 'respond']
        assert len(responds) >= 1

    def test_named_action(self, action_extractor):
        code = '''
const increment = assign({ count: ({ context }) => context.count + 1 });
'''
        result = action_extractor.extract(code, "named.ts")
        actions = result.get('actions', [])
        named = [a for a in actions if a.is_named]
        assert len(named) >= 1


# ═══════════════════════════════════════════════════════════════════
# Guard Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestXstateGuardExtractor:
    """Tests for XstateGuardExtractor."""

    def test_cond_guard_v4(self, guard_extractor):
        code = '''
const machine = createMachine({
    states: {
        idle: {
            on: {
                SUBMIT: { target: 'submitting', cond: 'isValid' },
            },
        },
    },
});
'''
        result = guard_extractor.extract(code, "cond.ts")
        guards = result.get('guards', [])
        assert len(guards) >= 1
        cond_guards = [g for g in guards if g.guard_type == 'cond']
        assert len(cond_guards) >= 1

    def test_guard_v5(self, guard_extractor):
        code = '''
const machine = createMachine({
    states: {
        idle: {
            on: {
                SUBMIT: { target: 'submitting', guard: 'isValid' },
            },
        },
    },
});
'''
        result = guard_extractor.extract(code, "guard.ts")
        guards = result.get('guards', [])
        assert len(guards) >= 1
        v5_guards = [g for g in guards if g.guard_type == 'guard']
        assert len(v5_guards) >= 1

    def test_not_guard_combinator(self, guard_extractor):
        code = '''
import { not } from 'xstate';

const notAdmin = not('isAdmin');
'''
        result = guard_extractor.extract(code, "not.ts")
        guards = result.get('guards', [])
        not_guards = [g for g in guards if g.guard_type == 'not']
        assert len(not_guards) >= 1

    def test_and_guard_combinator(self, guard_extractor):
        code = '''
import { and } from 'xstate';

const canSubmit = and(['isValid', 'isAuthenticated']);
'''
        result = guard_extractor.extract(code, "and.ts")
        guards = result.get('guards', [])
        and_guards = [g for g in guards if g.guard_type == 'and']
        assert len(and_guards) >= 1

    def test_or_guard_combinator(self, guard_extractor):
        code = '''
import { or } from 'xstate';

const canAccess = or(['isAdmin', 'isOwner']);
'''
        result = guard_extractor.extract(code, "or.ts")
        guards = result.get('guards', [])
        or_guards = [g for g in guards if g.guard_type == 'or']
        assert len(or_guards) >= 1

    def test_state_in_guard(self, guard_extractor):
        code = '''
import { stateIn } from 'xstate';

const isInEditMode = stateIn({ editor: 'editing' });
'''
        result = guard_extractor.extract(code, "stateIn.ts")
        guards = result.get('guards', [])
        si_guards = [g for g in guards if g.guard_type == 'stateIn']
        assert len(si_guards) >= 1

    def test_guard_definition_in_setup(self, guard_extractor):
        code = '''
const machine = setup({
    guards: {
        isValid: ({ context }) => context.email.includes('@'),
        isMax: ({ context }) => context.count >= 100,
    },
}).createMachine({
    id: 'form',
    initial: 'idle',
    states: { idle: {} },
});
'''
        result = guard_extractor.extract(code, "setup-guards.ts")
        guards = result.get('guards', [])
        assert len(guards) >= 1

    def test_inline_function_guard(self, guard_extractor):
        code = '''
const machine = createMachine({
    states: {
        idle: {
            on: {
                SUBMIT: {
                    target: 'done',
                    cond: (context, event) => context.isReady,
                },
            },
        },
    },
});
'''
        result = guard_extractor.extract(code, "inline.ts")
        guards = result.get('guards', [])
        assert len(guards) >= 1


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestXstateApiExtractor:
    """Tests for XstateApiExtractor."""

    def test_basic_imports(self, api_extractor):
        code = '''
import { createMachine, assign, interpret } from 'xstate';
import { useMachine } from '@xstate/react';
'''
        result = api_extractor.extract(code, "imports.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 2
        sources = [imp.source for imp in imports]
        assert 'xstate' in sources
        assert '@xstate/react' in sources

    def test_import_subpaths(self, api_extractor):
        code = '''
import { fromPromise, fromCallback } from 'xstate/actors';
import { createStore } from '@xstate/store';
'''
        result = api_extractor.extract(code, "subpath.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 1

    def test_create_actor_v5(self, api_extractor):
        code = '''
import { createActor } from 'xstate';

const machine = createMachine({ id: 'test', initial: 'idle', states: { idle: {} } });
const actor = createActor(machine, { input: { userId: '123' } });
actor.subscribe((snapshot) => console.log(snapshot.value));
actor.start();
'''
        result = api_extractor.extract(code, "createActor.ts")
        actors = result.get('actors', [])
        create_actors = [a for a in actors if a.creation_method == 'createActor']
        assert len(create_actors) >= 1

    def test_interpret_v4(self, api_extractor):
        code = '''
import { interpret } from 'xstate';

const service = interpret(toggleMachine)
    .onTransition((state) => console.log(state.value))
    .start();
'''
        result = api_extractor.extract(code, "interpret.ts")
        actors = result.get('actors', [])
        interps = [a for a in actors if a.creation_method == 'interpret']
        assert len(interps) >= 1

    def test_use_machine_react(self, api_extractor):
        code = '''
import { useMachine } from '@xstate/react';

function Toggle() {
    const [state, send] = useMachine(toggleMachine);
    return <button onClick={() => send('TOGGLE')}>{state.value}</button>;
}
'''
        result = api_extractor.extract(code, "component.tsx")
        actors = result.get('actors', [])
        hooks = [a for a in actors if a.creation_method == 'useMachine']
        assert len(hooks) >= 1

    def test_use_actor_react(self, api_extractor):
        code = '''
import { useActor } from '@xstate/react';

function Counter({ actorRef }) {
    const [state, send] = useActor(actorRef);
    return <div>{state.context.count}</div>;
}
'''
        result = api_extractor.extract(code, "useActor.tsx")
        actors = result.get('actors', [])
        ua = [a for a in actors if a.creation_method == 'useActor']
        assert len(ua) >= 1

    def test_use_selector_react(self, api_extractor):
        code = '''
import { useSelector } from '@xstate/react';

function Count({ actorRef }) {
    const count = useSelector(actorRef, (snapshot) => snapshot.context.count);
    return <div>{count}</div>;
}
'''
        result = api_extractor.extract(code, "useSelector.tsx")
        actors = result.get('actors', [])
        selectors = [a for a in actors if a.creation_method == 'useSelector']
        assert len(selectors) >= 1

    def test_from_promise(self, api_extractor):
        code = '''
import { fromPromise } from 'xstate';

const fetchUser = fromPromise(async ({ input }) => {
    const res = await fetch(`/api/users/${input.id}`);
    return res.json();
});
'''
        result = api_extractor.extract(code, "fromPromise.ts")
        actors = result.get('actors', [])
        promises = [a for a in actors if a.creation_method == 'fromPromise']
        assert len(promises) >= 1

    def test_from_callback(self, api_extractor):
        code = '''
import { fromCallback } from 'xstate';

const socketActor = fromCallback(({ sendBack, receive }) => {
    const ws = new WebSocket('ws://example.com');
    ws.onmessage = (msg) => sendBack({ type: 'MESSAGE', data: msg.data });
    return () => ws.close();
});
'''
        result = api_extractor.extract(code, "fromCallback.ts")
        actors = result.get('actors', [])
        callbacks = [a for a in actors if a.creation_method == 'fromCallback']
        assert len(callbacks) >= 1

    def test_from_observable(self, api_extractor):
        code = '''
import { fromObservable } from 'xstate';
import { interval } from 'rxjs';

const ticker = fromObservable(() => interval(1000));
'''
        result = api_extractor.extract(code, "fromObservable.ts")
        actors = result.get('actors', [])
        observables = [a for a in actors if a.creation_method == 'fromObservable']
        assert len(observables) >= 1

    def test_from_transition(self, api_extractor):
        code = '''
import { fromTransition } from 'xstate';

const reducer = fromTransition((state, event) => {
    if (event.type === 'INC') return { ...state, count: state.count + 1 };
    return state;
}, { count: 0 });
'''
        result = api_extractor.extract(code, "fromTransition.ts")
        actors = result.get('actors', [])
        transitions = [a for a in actors if a.creation_method == 'fromTransition']
        assert len(transitions) >= 1

    def test_spawn(self, api_extractor):
        code = '''
const parentMachine = createMachine({
    context: { childRef: null },
    on: {
        SPAWN: {
            actions: assign({
                childRef: () => spawn(childMachine, { id: 'child' }),
            }),
        },
    },
});
'''
        result = api_extractor.extract(code, "spawn.ts")
        actors = result.get('actors', [])
        spawned = [a for a in actors if a.creation_method == 'spawn']
        assert len(spawned) >= 1

    def test_typegen_tsTypes(self, api_extractor):
        code = '''
const machine = createMachine({
    tsTypes: {} as import('./machine.typegen').Typegen0,
    schema: {
        context: {} as { count: number },
        events: {} as { type: 'INC' } | { type: 'DEC' },
    },
});
'''
        result = api_extractor.extract(code, "typegen.ts")
        typegens = result.get('typegens', [])
        assert len(typegens) >= 1

    def test_subscribe_start_stop(self, api_extractor):
        code = '''
const actor = createActor(machine);
actor.subscribe((snapshot) => console.log(snapshot.value));
actor.start();

// later
actor.stop();
'''
        result = api_extractor.extract(code, "lifecycle.ts")
        actors = result.get('actors', [])
        ca = [a for a in actors if a.creation_method == 'createActor']
        assert len(ca) >= 1
        if ca:
            assert ca[0].has_subscribe is True

    def test_multiple_imports(self, api_extractor):
        code = '''
import { createMachine, assign, createActor, setup } from 'xstate';
import { fromPromise, fromCallback } from 'xstate';
import { useMachine, useActor, useSelector } from '@xstate/react';
import { createBrowserInspector } from '@stately/inspect';
'''
        result = api_extractor.extract(code, "multi-imports.ts")
        imports = result.get('imports', [])
        assert len(imports) >= 3


# ═══════════════════════════════════════════════════════════════════
# EnhancedXstateParser Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedXstateParser:
    """Tests for the integrated EnhancedXstateParser."""

    def test_is_xstate_file(self, parser):
        assert parser.is_xstate_file("import { createMachine } from 'xstate';")
        assert parser.is_xstate_file("import { useMachine } from '@xstate/react';")
        assert parser.is_xstate_file("import { setup } from 'xstate';")
        assert parser.is_xstate_file("import { createActor } from 'xstate';")
        assert not parser.is_xstate_file("import React from 'react';")
        assert not parser.is_xstate_file("const x = 1;")

    def test_parse_basic_machine(self, parser):
        code = '''
import { createMachine } from 'xstate';

const toggleMachine = createMachine({
    id: 'toggle',
    initial: 'inactive',
    states: {
        inactive: { on: { TOGGLE: 'active' } },
        active: { on: { TOGGLE: 'inactive' } },
    },
});
'''
        result = parser.parse(code, "toggle.ts")
        assert isinstance(result, XstateParseResult)
        assert result.file_path == "toggle.ts"
        assert len(result.machines) >= 1
        assert 'xstate' in result.detected_frameworks

    def test_parse_full_v5_machine(self, parser):
        code = '''
import { setup, assign, createActor, fromPromise, emit } from 'xstate';
import { useMachine, useSelector } from '@xstate/react';

const fetchMachine = setup({
    types: {} as {
        context: { data: null | string; error: null | string };
        events: { type: 'FETCH' } | { type: 'RETRY' };
    },
    actions: {
        setData: assign({ data: ({ event }) => event.output }),
        clearError: assign({ error: null }),
    },
    guards: {
        hasError: ({ context }) => context.error !== null,
    },
    actors: {
        fetchData: fromPromise(async () => {
            const res = await fetch('/api/data');
            return res.json();
        }),
    },
}).createMachine({
    id: 'fetch',
    initial: 'idle',
    context: { data: null, error: null },
    states: {
        idle: { on: { FETCH: 'loading' } },
        loading: {
            invoke: {
                src: 'fetchData',
                onDone: { target: 'success', actions: 'setData' },
                onError: { target: 'error' },
            },
        },
        success: { type: 'final' },
        error: {
            on: { RETRY: 'loading' },
        },
    },
});

const actor = createActor(fetchMachine);
actor.start();
'''
        result = parser.parse(code, "fetch.ts")
        assert len(result.machines) >= 1
        assert len(result.imports) >= 1
        assert len(result.actions) >= 1
        assert len(result.guards) >= 1
        assert len(result.actors) >= 1
        assert 'xstate' in result.detected_frameworks

    def test_detect_frameworks_react(self, parser):
        code = '''
import { useMachine } from '@xstate/react';
import { createMachine } from 'xstate';
'''
        result = parser.parse(code, "react.tsx")
        assert 'xstate' in result.detected_frameworks
        assert '@xstate/react' in result.detected_frameworks

    def test_detect_frameworks_vue(self, parser):
        code = '''
import { useMachine } from '@xstate/vue';
import { createMachine } from 'xstate';
'''
        result = parser.parse(code, "vue.ts")
        assert '@xstate/vue' in result.detected_frameworks

    def test_detect_frameworks_svelte(self, parser):
        code = '''
import { useMachine } from '@xstate/svelte';
import { createMachine } from 'xstate';
'''
        result = parser.parse(code, "svelte.ts")
        assert '@xstate/svelte' in result.detected_frameworks

    def test_detect_features(self, parser):
        code = '''
import { setup, assign, createActor, fromPromise } from 'xstate';

const machine = setup({
    types: {} as { context: { count: number } },
}).createMachine({
    id: 'test',
    type: 'parallel',
    context: { count: 0 },
    states: {
        a: {
            initial: 'idle',
            states: {
                idle: {
                    after: { 1000: 'done' },
                    always: [{ guard: 'check', target: 'done' }],
                },
                done: { type: 'final' },
            },
        },
    },
});
'''
        result = parser.parse(code, "features.ts")
        features = result.detected_features
        assert 'setup' in features
        assert 'assign' in features
        assert 'createActor' in features or 'create_actor' in features
        assert 'fromPromise' in features or 'from_promise' in features

    def test_detect_version_v5(self, parser):
        code = '''
import { setup, createActor, fromPromise, emit, enqueueActions } from 'xstate';
'''
        result = parser.parse(code, "v5.ts")
        assert result.xstate_version in ('v5', '5')

    def test_detect_version_v4(self, parser):
        code = '''
import { createMachine, interpret } from 'xstate';
const service = interpret(machine).start();
'''
        result = parser.parse(code, "v4.ts")
        # v4 uses interpret, not createActor
        assert result.xstate_version in ('v4', '4', 'v3-v4', 'unknown', '')

    def test_detect_version_v3(self, parser):
        code = '''
import { Machine, interpret } from 'xstate';
const lightMachine = Machine({ id: 'light', initial: 'green', states: { green: {} } });
'''
        result = parser.parse(code, "v3.ts")
        assert result.xstate_version in ('v3', '3', 'v3-v4', 'unknown', '')

    def test_parse_result_structure(self, parser):
        code = '''
import { createMachine } from 'xstate';
const m = createMachine({ id: 'test', initial: 'a', states: { a: {} } });
'''
        result = parser.parse(code, "struct.ts")
        assert hasattr(result, 'file_path')
        assert hasattr(result, 'file_type')
        assert hasattr(result, 'machines')
        assert hasattr(result, 'state_nodes')
        assert hasattr(result, 'transitions')
        assert hasattr(result, 'invokes')
        assert hasattr(result, 'actions')
        assert hasattr(result, 'guards')
        assert hasattr(result, 'imports')
        assert hasattr(result, 'actors')
        assert hasattr(result, 'typegens')
        assert hasattr(result, 'detected_frameworks')
        assert hasattr(result, 'detected_features')
        assert hasattr(result, 'xstate_version')

    def test_empty_file(self, parser):
        result = parser.parse("", "empty.ts")
        assert len(result.machines) == 0
        assert len(result.actions) == 0

    def test_non_xstate_file(self, parser):
        code = '''
import React from 'react';
function App() { return <div>Hello</div>; }
export default App;
'''
        result = parser.parse(code, "app.tsx")
        assert len(result.machines) == 0

    def test_complex_real_world_machine(self, parser):
        code = '''
import { setup, assign, createActor, fromPromise, fromCallback, sendTo, emit } from 'xstate';
import { useMachine, useSelector, useActorRef } from '@xstate/react';

interface AuthContext {
    user: User | null;
    error: string | null;
    token: string | null;
    retries: number;
}

type AuthEvent =
    | { type: 'LOGIN'; credentials: { email: string; password: string } }
    | { type: 'LOGOUT' }
    | { type: 'REFRESH_TOKEN' }
    | { type: 'SESSION_EXPIRED' };

const authMachine = setup({
    types: {} as {
        context: AuthContext;
        events: AuthEvent;
        input: { initialToken?: string };
    },
    actions: {
        setUser: assign({ user: ({ event }) => event.output.user, token: ({ event }) => event.output.token }),
        clearAuth: assign({ user: null, token: null, error: null }),
        setError: assign({ error: ({ event }) => event.error.message }),
        incrementRetries: assign({ retries: ({ context }) => context.retries + 1 }),
        notifyLogout: emit({ type: 'auth.logout' }),
    },
    guards: {
        canRetry: ({ context }) => context.retries < 3,
        hasToken: ({ context }) => context.token !== null,
        isTokenExpired: ({ context }) => isExpired(context.token),
    },
    actors: {
        loginService: fromPromise(async ({ input }) => {
            const res = await api.login(input.email, input.password);
            return { user: res.user, token: res.token };
        }),
        tokenRefreshService: fromPromise(async ({ input }) => {
            return await api.refreshToken(input.token);
        }),
        sessionMonitor: fromCallback(({ sendBack }) => {
            const interval = setInterval(() => sendBack({ type: 'CHECK_SESSION' }), 60000);
            return () => clearInterval(interval);
        }),
    },
}).createMachine({
    id: 'auth',
    initial: 'idle',
    context: ({ input }) => ({
        user: null,
        error: null,
        token: input.initialToken ?? null,
        retries: 0,
    }),
    states: {
        idle: {
            always: [
                { guard: 'hasToken', target: 'authenticated' },
            ],
            on: { LOGIN: 'authenticating' },
        },
        authenticating: {
            entry: ['clearAuth'],
            invoke: {
                id: 'loginService',
                src: 'loginService',
                input: ({ event }) => event.credentials,
                onDone: { target: 'authenticated', actions: 'setUser' },
                onError: [
                    { guard: 'canRetry', target: 'retrying', actions: 'incrementRetries' },
                    { target: 'error', actions: 'setError' },
                ],
            },
        },
        authenticated: {
            type: 'parallel',
            states: {
                session: {
                    invoke: { src: 'sessionMonitor', id: 'monitor' },
                    on: {
                        SESSION_EXPIRED: '#auth.idle',
                        CHECK_SESSION: [
                            { guard: 'isTokenExpired', target: '#auth.refreshing' },
                        ],
                    },
                },
                activity: {
                    initial: 'active',
                    states: {
                        active: {
                            after: { 1800000: 'idle' },
                            on: { USER_ACTIVITY: 'active' },
                        },
                        idle: {
                            tags: ['idle'],
                            after: { 300000: '#auth.idle' },
                        },
                    },
                },
            },
            on: { LOGOUT: { target: 'idle', actions: ['clearAuth', 'notifyLogout'] } },
        },
        refreshing: {
            invoke: {
                src: 'tokenRefreshService',
                input: ({ context }) => ({ token: context.token }),
                onDone: { target: 'authenticated', actions: 'setUser' },
                onError: { target: 'idle', actions: 'clearAuth' },
            },
        },
        retrying: {
            after: { 2000: 'authenticating' },
        },
        error: {
            entry: 'setError',
            on: { LOGIN: 'authenticating' },
        },
    },
});

export function useAuth() {
    const [state, send] = useMachine(authMachine);
    const isLoading = useSelector(state, (s) => s.hasTag('loading'));
    return { state, send, isLoading };
}
'''
        result = parser.parse(code, "auth.machine.ts")
        assert len(result.machines) >= 1
        assert len(result.imports) >= 2
        assert len(result.actions) >= 3
        assert len(result.guards) >= 2
        assert len(result.state_nodes) >= 3
        assert 'xstate' in result.detected_frameworks
        assert '@xstate/react' in result.detected_frameworks

    def test_xstate_inspect(self, parser):
        code = '''
import { createMachine } from 'xstate';
import { createBrowserInspector } from '@stately/inspect';

const inspector = createBrowserInspector();
'''
        result = parser.parse(code, "inspect.ts")
        assert '@stately/inspect' in result.detected_frameworks or '@xstate/inspect' in result.detected_frameworks

    def test_xstate_test_integration(self, parser):
        code = '''
import { createMachine } from 'xstate';
import { createTestModel } from '@xstate/test';

const machine = createMachine({ id: 'test', initial: 'a', states: { a: {} } });
const model = createTestModel(machine);
'''
        result = parser.parse(code, "test.spec.ts")
        assert '@xstate/test' in result.detected_frameworks

    def test_xstate_store(self, parser):
        code = '''
import { createStore } from '@xstate/store';

const countStore = createStore({ count: 0 }, {
    inc: (context) => ({ count: context.count + 1 }),
});
'''
        result = parser.parse(code, "store.ts")
        assert '@xstate/store' in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestXstateIntegration:
    """Integration tests combining multiple extractors."""

    def test_parser_delegates_to_all_extractors(self, parser):
        """Verify parser uses all 5 extractors."""
        code = '''
import { createMachine, assign, createActor } from 'xstate';
import { useMachine } from '@xstate/react';

const machine = createMachine({
    id: 'integration',
    initial: 'idle',
    context: { count: 0 },
    states: {
        idle: {
            on: {
                START: { target: 'active', guard: 'isReady', actions: assign({ count: 1 }) },
            },
        },
        active: {
            invoke: { src: 'fetchData', onDone: 'done', onError: 'error' },
        },
        done: { type: 'final' },
        error: {},
    },
});

const actor = createActor(machine);
'''
        result = parser.parse(code, "integration.ts")
        # Machine extractor
        assert len(result.machines) >= 1
        # State extractor
        assert len(result.state_nodes) >= 1
        # Action extractor
        assert len(result.actions) >= 1
        # Guard extractor
        assert len(result.guards) >= 1
        # API extractor
        assert len(result.imports) >= 1
        assert len(result.actors) >= 1

    def test_v4_to_v5_patterns_coexist(self, parser):
        """Test file with both v4 and v5 patterns (migration in progress)."""
        code = '''
import { createMachine, interpret, assign, createActor } from 'xstate';

// v4 style
const legacyMachine = createMachine({
    id: 'legacy',
    initial: 'idle',
    predictableActionArguments: true,
    states: {
        idle: {
            on: { GO: { target: 'active', cond: 'check' } },
        },
        active: {},
    },
});
const legacyService = interpret(legacyMachine).start();

// v5 style
const modernMachine = createMachine({
    id: 'modern',
    initial: 'idle',
    states: {
        idle: {
            on: { GO: { target: 'active', guard: 'check' } },
        },
        active: {},
    },
});
const modernActor = createActor(modernMachine);
modernActor.start();
'''
        result = parser.parse(code, "migration.ts")
        assert len(result.machines) >= 2
        assert len(result.actors) >= 2  # interpret + createActor
        # Both cond and guard detected
        cond_guards = [g for g in result.guards if g.guard_type == 'cond']
        v5_guards = [g for g in result.guards if g.guard_type == 'guard']
        assert len(cond_guards) >= 1 or len(v5_guards) >= 1

    def test_dataclass_fields(self, parser):
        """Verify XstateParseResult dataclass has all expected fields."""
        result = XstateParseResult(
            file_path="test.ts",
            file_type="typescript",
        )
        assert result.machines == []
        assert result.state_nodes == []
        assert result.transitions == []
        assert result.invokes == []
        assert result.actions == []
        assert result.guards == []
        assert result.imports == []
        assert result.actors == []
        assert result.typegens == []
        assert result.detected_frameworks == []
        assert result.detected_features == []
        assert result.xstate_version == ""

    def test_extractor_dataclass_fields(self):
        """Verify all extractor dataclasses can be instantiated."""
        machine = XstateMachineInfo(name="test", creation_method="createMachine")
        assert machine.name == "test"
        assert machine.machine_id == ""
        assert machine.initial_state == ""
        assert machine.has_context is False

        state = XstateStateNodeInfo(name="idle")
        assert state.name == "idle"
        assert state.state_type == "atomic"
        assert state.has_entry is False

        transition = XstateTransitionInfo(event="CLICK", source_state="idle")
        assert transition.event == "CLICK"
        assert transition.has_guard is False

        invoke = XstateInvokeInfo(name="fetchService")
        assert invoke.name == "fetchService"
        assert invoke.invoke_type == ""

        action = XstateActionInfo(name="increment", action_type="assign")
        assert action.name == "increment"
        assert action.is_named is False

        guard = XstateGuardInfo(name="isValid", guard_type="guard")
        assert guard.name == "isValid"
        assert guard.is_negated is False

        imp = XstateImportInfo(source="xstate")
        assert imp.source == "xstate"
        assert imp.imported_names == []

        actor = XstateActorInfo(name="service", creation_method="createActor")
        assert actor.name == "service"
        assert actor.has_subscribe is False

        tg = XstateTypegenInfo()
        assert tg.typegen_type == ""
        assert tg.has_context_type is False
