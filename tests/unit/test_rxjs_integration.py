"""
Tests for RxJS Reactive Programming integration.

Tests cover:
- All 5 extractors (operator, observable, subject, scheduler, api)
- Parser (EnhancedRxjsParser)
- Scanner integration (ProjectMatrix fields, _parse_rxjs)
- Compressor integration ([RXJS_*] sections)
"""

import os
import pytest
from codetrellis.extractors.rxjs import (
    RxjsOperatorExtractor,
    RxjsObservableExtractor,
    RxjsSubjectExtractor,
    RxjsSchedulerExtractor,
    RxjsAPIExtractor,
)
from codetrellis.rxjs_parser_enhanced import (
    EnhancedRxjsParser,
    RxjsParseResult,
)


# ═══════════════════════════════════════════════════════════════════════
# Operator Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRxjsOperatorExtractor:
    """Tests for RxjsOperatorExtractor."""

    def setup_method(self):
        self.extractor = RxjsOperatorExtractor()

    def test_pipeable_operators(self):
        code = '''
import { map, filter, switchMap } from 'rxjs/operators';

data$.pipe(
  filter(x => x > 0),
  map(x => x * 2),
  switchMap(x => fetchData(x)),
);
'''
        result = self.extractor.extract(code, "service.ts")
        assert len(result['operators']) >= 3
        cats = {op.category for op in result['operators']}
        assert 'filtering' in cats
        assert 'higher_order' in cats  # switchMap

    def test_creation_operators(self):
        code = '''
import { of, from, interval } from 'rxjs';

const source$ = of(1, 2, 3);
const fromArr$ = from([1, 2, 3]);
const tick$ = interval(1000);
'''
        result = self.extractor.extract(code, "service.ts")
        assert len(result['operators']) >= 1

    def test_pipe_chain(self):
        code = '''
import { map, filter, debounceTime, catchError } from 'rxjs/operators';

input$.pipe(
  debounceTime(300),
  filter(value => value.length > 2),
  map(value => value.trim()),
  catchError(err => of(null)),
);
'''
        result = self.extractor.extract(code, "search.ts")
        assert len(result['pipes']) >= 1
        pipe = result['pipes'][0]
        assert pipe.operator_count >= 4

    def test_error_handling_operators(self):
        code = '''
import { catchError, retry } from 'rxjs/operators';

http.get('/api').pipe(
  retry(3),
  catchError(err => throwError(() => err)),
);
'''
        result = self.extractor.extract(code, "api.ts")
        ops = [op for op in result['operators'] if op.category == 'error']
        assert len(ops) >= 1

    def test_combination_operators(self):
        code = '''
import { combineLatest, merge, forkJoin, of } from 'rxjs';
import { combineLatestWith, mergeWith } from 'rxjs/operators';

const combined$ = a$.pipe(
  combineLatestWith(b$),
  mergeWith(c$),
);
'''
        result = self.extractor.extract(code, "state.ts")
        assert len(result['operators']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Observable Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRxjsObservableExtractor:
    """Tests for RxjsObservableExtractor."""

    def setup_method(self):
        self.extractor = RxjsObservableExtractor()

    def test_observable_constructor(self):
        code = '''
const source$ = new Observable(subscriber => {
  subscriber.next(1);
  subscriber.complete();
});
'''
        result = self.extractor.extract(code, "custom.ts")
        assert len(result['observables']) >= 1
        assert result['observables'][0].creation_method == 'constructor'

    def test_subscribe_with_observer(self):
        code = '''
source.subscribe({
  next: value => console.log(value),
  error: err => console.error(err),
  complete: () => console.log('done'),
});
'''
        result = self.extractor.extract(code, "sub.ts")
        assert len(result['subscriptions']) >= 1
        sub = result['subscriptions'][0]
        assert sub.has_error is True
        assert sub.has_complete is True

    def test_subscribe_with_unsubscribe(self):
        code = '''
const sub = source.subscribe(val => console.log(val));
sub.unsubscribe();
'''
        result = self.extractor.extract(code, "cleanup.ts")
        assert len(result['subscriptions']) >= 1
        assert result['subscriptions'][0].is_unsubscribed is True

    def test_to_promise_deprecated(self):
        code = '''
const value = await source.toPromise();
'''
        result = self.extractor.extract(code, "legacy.ts")
        assert len(result['conversions']) >= 1
        assert result['conversions'][0].conversion_type == 'toPromise'

    def test_first_value_from(self):
        code = '''
import { firstValueFrom } from 'rxjs';
const value = await firstValueFrom(source);
'''
        result = self.extractor.extract(code, "modern.ts")
        assert len(result['conversions']) >= 1
        assert result['conversions'][0].conversion_type == 'firstValueFrom'

    def test_take_until_cleanup(self):
        code = '''
source.pipe(
  takeUntil(this.destroy)
).subscribe();
'''
        result = self.extractor.extract(code, "comp.ts")
        assert len(result['subscription_mgmt']) >= 1
        assert result['subscription_mgmt'][0].pattern == 'takeUntil'


# ═══════════════════════════════════════════════════════════════════════
# Subject Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRxjsSubjectExtractor:
    """Tests for RxjsSubjectExtractor."""

    def setup_method(self):
        self.extractor = RxjsSubjectExtractor()

    def test_basic_subject(self):
        code = '''
const subject = new Subject();
subject.next(1);
subject.next(2);
subject.complete();
'''
        result = self.extractor.extract(code, "state.ts")
        assert len(result['subjects']) >= 1
        subj = result['subjects'][0]
        assert subj.subject_type == 'Subject'
        assert subj.next_count >= 2
        assert subj.has_complete_call is True

    def test_behavior_subject(self):
        code = '''
const counter = new BehaviorSubject(0);
counter.next(1);
'''
        result = self.extractor.extract(code, "state.ts")
        assert len(result['subjects']) >= 1
        subj = result['subjects'][0]
        assert subj.subject_type == 'BehaviorSubject'
        assert subj.initial_value == '0'

    def test_replay_subject(self):
        code = '''
const buffer = new ReplaySubject(3, 500);
'''
        result = self.extractor.extract(code, "cache.ts")
        assert len(result['subjects']) >= 1
        subj = result['subjects'][0]
        assert subj.subject_type == 'ReplaySubject'
        assert subj.buffer_size == '3'

    def test_async_subject(self):
        code = '''
const last = new AsyncSubject();
last.next(1);
last.next(2);
last.complete();
'''
        result = self.extractor.extract(code, "async.ts")
        assert len(result['subjects']) >= 1
        assert result['subjects'][0].subject_type == 'AsyncSubject'

    def test_emissions(self):
        code = '''
subject.next("hello");
subject.error(new Error("fail"));
subject.complete();
'''
        result = self.extractor.extract(code, "emit.ts")
        types = {em.emission_type for em in result['emissions']}
        assert 'next' in types
        assert 'error' in types
        assert 'complete' in types


# ═══════════════════════════════════════════════════════════════════════
# Scheduler Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRxjsSchedulerExtractor:
    """Tests for RxjsSchedulerExtractor."""

    def setup_method(self):
        self.extractor = RxjsSchedulerExtractor()

    def test_observe_on(self):
        code = '''
import { asyncScheduler } from 'rxjs';
import { observeOn } from 'rxjs/operators';
source.pipe(
  observeOn(asyncScheduler)
);
'''
        result = self.extractor.extract(code, "sched.ts")
        assert len(result['schedulers']) >= 1
        assert result['schedulers'][0].scheduler_type == 'async'
        assert result['schedulers'][0].usage_context == 'observeOn'

    def test_test_scheduler(self):
        code = '''
const scheduler = new TestScheduler((actual, expected) => {
  expect(actual).toEqual(expected);
});
'''
        result = self.extractor.extract(code, "spec.ts")
        assert len(result['testing']) >= 1

    def test_marble_testing(self):
        code = '''
scheduler.run(({ hot, cold, expectObservable }) => {
  const source = hot('--a--b--|');
  const expected = '--a--b--|';
  expectObservable(source).toBe(expected);
});
'''
        result = self.extractor.extract(code, "spec.ts")
        assert len(result['testing']) >= 1
        assert len(result['marbles']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRxjsAPIExtractor:
    """Tests for RxjsAPIExtractor."""

    def setup_method(self):
        self.extractor = RxjsAPIExtractor()

    def test_esm_imports(self):
        code = '''
import { Observable, of, from } from 'rxjs';
import { map, filter } from 'rxjs/operators';
'''
        result = self.extractor.extract(code, "service.ts")
        assert len(result['imports']) >= 2

    def test_type_imports(self):
        code = '''
import type { Observable, Subscription } from 'rxjs';
'''
        result = self.extractor.extract(code, "types.ts")
        assert len(result['types']) >= 1

    def test_angular_integration(self):
        code = '''
import { Component } from '@angular/core';
import { Observable } from 'rxjs';

@Component({ selector: 'app-root' })
export class AppComponent {
  data: Observable<string>;
}
'''
        result = self.extractor.extract(code, "comp.ts")
        assert len(result['integrations']) >= 1
        assert result['integrations'][0].integration_type == 'angular'

    def test_ngrx_integration(self):
        code = '''
import { createEffect, Actions, ofType } from '@ngrx/effects';
import { switchMap, catchError } from 'rxjs/operators';
'''
        result = self.extractor.extract(code, "effects.ts")
        assert len(result['integrations']) >= 1
        assert result['integrations'][0].integration_type == 'ngrx'

    def test_deprecation_detection(self):
        code = '''
const val = await source.toPromise();
const plucked = data.pipe(pluck('name'));
'''
        result = self.extractor.extract(code, "old.ts")
        assert len(result['deprecations']) >= 1

    def test_version_detection_v7(self):
        code = '''
import { firstValueFrom, of, map, filter } from 'rxjs';
of(1).pipe(map(x => x * 2), filter(x => x > 0));
'''
        result = self.extractor.extract(code, "modern.ts")
        assert result['version_info'].get('package') == 'rxjs-v7'

    def test_version_detection_v6(self):
        code = '''
import { Observable } from 'rxjs';
import { map, filter } from 'rxjs/operators';
'''
        result = self.extractor.extract(code, "v6.ts")
        assert result['version_info'].get('package') in ('rxjs-v6', 'rxjs')


# ═══════════════════════════════════════════════════════════════════════
# Parser Tests
# ═══════════════════════════════════════════════════════════════════════

class TestEnhancedRxjsParser:
    """Tests for EnhancedRxjsParser."""

    def setup_method(self):
        self.parser = EnhancedRxjsParser()

    def test_is_rxjs_file_positive(self):
        code = '''
import { Observable, of } from 'rxjs';
import { map, filter } from 'rxjs/operators';
'''
        assert self.parser.is_rxjs_file(code, "service.ts") is True

    def test_is_rxjs_file_negative(self):
        code = '''
const x = 42;
console.log(x);
'''
        assert self.parser.is_rxjs_file(code, "util.js") is False

    def test_is_rxjs_file_subject(self):
        code = '''
const state = new BehaviorSubject(null);
'''
        assert self.parser.is_rxjs_file(code, "store.ts") is True

    def test_full_parse(self):
        code = '''
import { Observable, Subject, of, from, combineLatest } from 'rxjs';
import { map, filter, switchMap, catchError, debounceTime, tap } from 'rxjs/operators';

const search = new Subject();

const results = search.pipe(
  debounceTime(300),
  filter(term => term.length > 2),
  switchMap(term => from(fetch(`/api/search?q=${term}`))),
  map(res => res.json()),
  catchError(err => of([])),
);

results.subscribe({
  next: results => console.log(results),
  error: err => console.error(err),
});
'''
        result = self.parser.parse(code, "search.ts")
        assert isinstance(result, RxjsParseResult)
        assert result.has_operators is True
        assert result.has_subjects is True
        assert result.has_pipes is True
        assert result.has_subscriptions is True
        assert result.has_higher_order is True
        assert result.has_error_handling is True
        assert result.has_typescript is True
        assert len(result.detected_features) >= 3

    def test_detected_frameworks(self):
        code = '''
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
'''
        result = self.parser.parse(code, "app.ts")
        assert 'rxjs' in result.detected_frameworks
        assert 'rxjs-operators' in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRxjsScannerIntegration:
    """Tests for RxJS scanner integration."""

    def test_project_matrix_has_rxjs_fields(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name="test", root_path=".")
        assert hasattr(matrix, 'rxjs_operators')
        assert hasattr(matrix, 'rxjs_subjects')
        assert hasattr(matrix, 'rxjs_observables')
        assert hasattr(matrix, 'rxjs_subscriptions')
        assert hasattr(matrix, 'rxjs_pipes')
        assert hasattr(matrix, 'rxjs_schedulers')
        assert hasattr(matrix, 'rxjs_imports')
        assert hasattr(matrix, 'rxjs_detected_frameworks')
        assert hasattr(matrix, 'rxjs_version')
        assert hasattr(matrix, 'rxjs_has_operators')
        assert hasattr(matrix, 'rxjs_has_subjects')
        assert hasattr(matrix, 'rxjs_has_pipes')

    def test_scanner_has_rxjs_parser(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner(".")
        assert hasattr(scanner, 'rxjs_parser')
        assert isinstance(scanner.rxjs_parser, EnhancedRxjsParser)

    def test_parse_rxjs_populates_matrix(self):
        import tempfile, os
        from pathlib import Path
        from codetrellis.scanner import ProjectScanner, ProjectMatrix

        code = '''
import { Observable, Subject, of } from 'rxjs';
import { map, filter } from 'rxjs/operators';

const data = new Subject();
const doubled = data.pipe(
  filter(x => x > 0),
  map(x => x * 2),
);
doubled.subscribe(val => console.log(val));
data.next(5);
'''
        with tempfile.NamedTemporaryFile(suffix=".ts", mode='w', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                scanner = ProjectScanner(".")
                matrix = ProjectMatrix(name="test", root_path=".")
                scanner._parse_rxjs(Path(f.name), matrix)
                assert len(matrix.rxjs_operators) >= 1
                assert len(matrix.rxjs_subjects) >= 1
                assert matrix.rxjs_has_operators is True
                assert matrix.rxjs_has_subjects is True
            finally:
                os.unlink(f.name)


# ═══════════════════════════════════════════════════════════════════════
# Compressor Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRxjsCompressorIntegration:
    """Tests for RxJS compressor integration."""

    def test_compress_rxjs_operators(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix

        matrix = ProjectMatrix(name="test", root_path=".")
        matrix.rxjs_operators = [
            {"name": "map", "file": "a.ts", "line": 1, "category": "transformation", "is_pipeable": True, "is_legacy": False},
            {"name": "filter", "file": "a.ts", "line": 2, "category": "filtering", "is_pipeable": True, "is_legacy": False},
            {"name": "switchMap", "file": "a.ts", "line": 3, "category": "higher_order", "is_pipeable": True, "is_legacy": False},
        ]
        matrix.rxjs_pipes = [
            {"name": "filter,map,switchMap", "file": "a.ts", "line": 1, "operator_count": 3},
        ]

        compressor = MatrixCompressor(matrix, ".")
        lines = compressor._compress_rxjs_operators(matrix)
        assert len(lines) >= 1

    def test_compress_rxjs_observables(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix

        matrix = ProjectMatrix(name="test", root_path=".")
        matrix.rxjs_observables = [
            {"name": "source$", "file": "a.ts", "line": 1, "creation_method": "constructor", "is_typed": True, "type_param": "number"},
        ]
        matrix.rxjs_subscriptions = [
            {"name": "sub", "file": "a.ts", "line": 5, "has_error": True, "has_complete": False, "is_unsubscribed": True},
        ]

        compressor = MatrixCompressor(matrix, ".")
        lines = compressor._compress_rxjs_observables(matrix)
        assert len(lines) >= 1

    def test_compress_rxjs_subjects(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix

        matrix = ProjectMatrix(name="test", root_path=".")
        matrix.rxjs_subjects = [
            {"name": "data$", "file": "a.ts", "line": 1, "subject_type": "BehaviorSubject",
             "type_param": "number", "has_as_observable": True, "next_count": 3},
        ]
        matrix.rxjs_emissions = [
            {"name": "data$", "file": "a.ts", "line": 5, "emission_type": "next"},
            {"name": "data$", "file": "a.ts", "line": 6, "emission_type": "next"},
        ]

        compressor = MatrixCompressor(matrix, ".")
        lines = compressor._compress_rxjs_subjects(matrix)
        assert len(lines) >= 1
        assert 'subjects(1)' in lines[0]

    def test_compress_rxjs_api(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix

        matrix = ProjectMatrix(name="test", root_path=".")
        matrix.rxjs_imports = [
            {"name": "Observable,of", "file": "a.ts", "line": 1, "source": "rxjs",
             "import_type": "esm", "subpath": ""},
        ]
        matrix.rxjs_detected_frameworks = ['rxjs']
        matrix.rxjs_detected_features = ['operators', 'subjects']
        matrix.rxjs_version = 'v7'
        matrix.rxjs_has_typescript = True
        matrix.rxjs_deprecations = [
            {"name": "toPromise", "file": "a.ts", "line": 10,
             "deprecated_in": "v7", "replacement": "firstValueFrom"},
        ]

        compressor = MatrixCompressor(matrix, ".")
        lines = compressor._compress_rxjs_api(matrix)
        assert len(lines) >= 1
        assert any('imports' in l for l in lines)
        assert any('RxJS version' in l for l in lines)
        assert any('deprecated' in l for l in lines)
