"""
Tests for GSAP Animation Platform integration.

Tests cover:
- All 5 extractors (animation, timeline, plugin, scroll, api)
- Parser (EnhancedGsapParser)
- Scanner integration (ProjectMatrix fields, _parse_gsap)
- Compressor integration ([GSAP_*] sections)
"""

import os
import pytest
from codetrellis.extractors.gsap import (
    GsapAnimationExtractor,
    GsapTimelineExtractor,
    GsapPluginExtractor,
    GsapScrollExtractor,
    GsapAPIExtractor,
)
from codetrellis.gsap_parser_enhanced import (
    EnhancedGsapParser,
    GsapParseResult,
)


# ═══════════════════════════════════════════════════════════════════════
# Animation Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestGsapAnimationExtractor:
    """Tests for GsapAnimationExtractor."""

    def setup_method(self):
        self.extractor = GsapAnimationExtractor()

    def test_gsap_to(self):
        code = '''
gsap.to(".box", { x: 100, duration: 1 });
'''
        result = self.extractor.extract(code, "anim.js")
        assert len(result['tweens']) >= 1
        tw = result['tweens'][0]
        assert tw.tween_type == 'to'
        assert tw.target == '.box'
        assert tw.has_duration is True

    def test_gsap_from(self):
        code = '''
gsap.from(".hero", { opacity: 0, y: 50, duration: 0.8 });
'''
        result = self.extractor.extract(code, "anim.js")
        assert len(result['tweens']) >= 1
        assert result['tweens'][0].tween_type == 'from'

    def test_gsap_fromTo(self):
        code = '''
gsap.fromTo(".element", { opacity: 0 }, { opacity: 1, duration: 1 });
'''
        result = self.extractor.extract(code, "anim.js")
        assert len(result['tweens']) >= 1
        assert result['tweens'][0].tween_type == 'fromTo'

    def test_gsap_set(self):
        code = '''
gsap.set(".element", { clearProps: "all" });
'''
        result = self.extractor.extract(code, "anim.js")
        assert len(result['sets']) >= 1

    def test_legacy_tweenmax(self):
        code = '''
TweenMax.to(".box", 1, { x: 100, ease: Power2.easeOut });
'''
        result = self.extractor.extract(code, "old.js")
        assert len(result['tweens']) >= 1
        tw = result['tweens'][0]
        assert tw.api_style == 'v1'

    def test_stagger(self):
        code = '''
gsap.to(".items", {
  y: 0,
  stagger: 0.1,
  duration: 0.5
});
'''
        result = self.extractor.extract(code, "anim.js")
        assert len(result['staggers']) >= 1

    def test_legacy_stagger_to(self):
        code = '''
TweenMax.staggerTo(".items", 0.5, { opacity: 1 }, 0.1);
'''
        result = self.extractor.extract(code, "old.js")
        assert len(result['staggers']) >= 1

    def test_ease_detection(self):
        code = '''
gsap.to(".box", { x: 100, ease: "elastic.out(1, 0.3)" });
gsap.to(".other", { y: 50, ease: "power2.inOut" });
'''
        result = self.extractor.extract(code, "anim.js")
        assert len(result['eases']) >= 1

    def test_scroll_trigger_in_tween(self):
        code = '''
gsap.to(".panel", {
  x: 300,
  scrollTrigger: {
    trigger: ".panel",
    start: "top top",
    scrub: true,
  }
});
'''
        result = self.extractor.extract(code, "scroll.js")
        assert len(result['tweens']) >= 1
        assert result['tweens'][0].has_scrollTrigger is True


# ═══════════════════════════════════════════════════════════════════════
# Timeline Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestGsapTimelineExtractor:
    """Tests for GsapTimelineExtractor."""

    def setup_method(self):
        self.extractor = GsapTimelineExtractor()

    def test_basic_timeline(self):
        code = '''
const tl = gsap.timeline();
tl.to(".box1", { x: 100 })
  .to(".box2", { y: 50 });
'''
        result = self.extractor.extract(code, "timeline.js")
        assert len(result['timelines']) >= 1
        assert result['timelines'][0].name == 'tl'

    def test_timeline_with_defaults(self):
        code = '''
const tl = gsap.timeline({ defaults: { duration: 0.5 } });
'''
        result = self.extractor.extract(code, "timeline.js")
        assert len(result['timelines']) >= 1
        assert result['timelines'][0].has_defaults is True

    def test_timeline_with_scrolltrigger(self):
        code = '''
const tl = gsap.timeline({
  scrollTrigger: {
    trigger: ".section",
    start: "top top",
    pin: true,
  }
});
'''
        result = self.extractor.extract(code, "scroll.js")
        assert len(result['timelines']) >= 1
        assert result['timelines'][0].has_scrollTrigger is True

    def test_timeline_with_repeat(self):
        code = '''
const tl = gsap.timeline({ repeat: -1, yoyo: true });
'''
        result = self.extractor.extract(code, "timeline.js")
        assert len(result['timelines']) >= 1
        tl = result['timelines'][0]
        assert tl.has_repeat is True
        assert tl.has_yoyo is True

    def test_legacy_timeline_max(self):
        code = '''
var tl = new TimelineMax({ repeat: 2 });
'''
        result = self.extractor.extract(code, "old.js")
        assert len(result['timelines']) >= 1
        assert result['timelines'][0].api_style in ('v1', 'v2')

    def test_labels(self):
        code = '''
const tl = gsap.timeline();
tl.addLabel("start")
  .to(".box", { x: 100 })
  .addLabel("middle")
  .to(".box", { y: 50 });
'''
        result = self.extractor.extract(code, "timeline.js")
        assert len(result['labels']) >= 1

    def test_callbacks(self):
        code = '''
const tl = gsap.timeline({ onComplete: done, onUpdate: tick });
'''
        result = self.extractor.extract(code, "timeline.js")
        assert len(result['callbacks']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Plugin Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestGsapPluginExtractor:
    """Tests for GsapPluginExtractor."""

    def setup_method(self):
        self.extractor = GsapPluginExtractor()

    def test_register_plugin(self):
        code = '''
gsap.registerPlugin(ScrollTrigger, Flip, SplitText);
'''
        result = self.extractor.extract(code, "setup.js")
        assert len(result['registrations']) >= 1
        reg = result['registrations'][0]
        assert 'ScrollTrigger' in reg.plugins

    def test_register_effect(self):
        code = '''
gsap.registerEffect({
  name: "fade",
  effect: (targets, config) => gsap.to(targets, { opacity: 0 }),
  defaults: { duration: 1 },
});
'''
        result = self.extractor.extract(code, "setup.js")
        assert len(result['effects']) >= 1
        assert result['effects'][0].name == 'fade'

    def test_utility_detection(self):
        code = '''
const items = gsap.utils.toArray(".item");
const clamp = gsap.utils.clamp(0, 100);
'''
        result = self.extractor.extract(code, "utils.js")
        assert len(result['utilities']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Scroll Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestGsapScrollExtractor:
    """Tests for GsapScrollExtractor."""

    def setup_method(self):
        self.extractor = GsapScrollExtractor()

    def test_scroll_trigger_create(self):
        code = '''
ScrollTrigger.create({
  trigger: ".section",
  start: "top top",
  end: "bottom bottom",
  pin: true,
  scrub: 1,
  markers: true,
});
'''
        result = self.extractor.extract(code, "scroll.js")
        assert len(result['scroll_triggers']) >= 1
        st = result['scroll_triggers'][0]
        assert st.has_pin is True
        assert st.has_scrub is True

    def test_scroll_smoother(self):
        code = '''
ScrollSmoother.create({
  smooth: 1.5,
  effects: true,
});
'''
        result = self.extractor.extract(code, "scroll.js")
        assert len(result['smoothers']) >= 1
        assert result['smoothers'][0].has_effects is True

    def test_observer(self):
        code = '''
Observer.create({
  type: "wheel,touch",
  onUp: () => goToSection(currentIndex - 1),
  onDown: () => goToSection(currentIndex + 1),
});
'''
        result = self.extractor.extract(code, "scroll.js")
        assert len(result['observers']) >= 1

    def test_scroll_batch(self):
        code = '''
ScrollTrigger.batch(".item", {
  onEnter: (batch) => gsap.to(batch, { opacity: 1, stagger: 0.1 }),
});
'''
        result = self.extractor.extract(code, "scroll.js")
        assert len(result['batches']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestGsapAPIExtractor:
    """Tests for GsapAPIExtractor."""

    def setup_method(self):
        self.extractor = GsapAPIExtractor()

    def test_esm_import(self):
        code = '''
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
'''
        result = self.extractor.extract(code, "app.ts")
        assert len(result['imports']) >= 2
        assert result['imports'][0].import_type == 'esm'

    def test_cjs_require(self):
        code = '''
const gsap = require("gsap");
'''
        result = self.extractor.extract(code, "app.js")
        assert len(result['imports']) >= 1
        assert result['imports'][0].import_type == 'cjs'

    def test_react_integration(self):
        code = '''
import { useGSAP } from "@gsap/react";
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['integrations']) >= 1
        assert result['integrations'][0].integration_type == 'react'

    def test_gsap_context(self):
        code = '''
const ctx = gsap.context(() => {
  gsap.to(".box", { x: 100 });
}, containerRef);
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['contexts']) >= 1

    def test_gsap_match_media(self):
        code = '''
let mm = gsap.matchMedia();
mm.add("(min-width: 768px)", () => {
  gsap.to(".box", { x: 200 });
});
'''
        result = self.extractor.extract(code, "responsive.js")
        assert len(result['match_medias']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Parser Tests
# ═══════════════════════════════════════════════════════════════════════

class TestEnhancedGsapParser:
    """Tests for EnhancedGsapParser."""

    def setup_method(self):
        self.parser = EnhancedGsapParser()

    def test_is_gsap_file_positive(self):
        code = '''
import { gsap } from "gsap";
gsap.to(".box", { x: 100 });
'''
        assert self.parser.is_gsap_file(code, "app.js") is True

    def test_is_gsap_file_negative(self):
        code = '''
const x = 42;
console.log(x);
'''
        assert self.parser.is_gsap_file(code, "app.js") is False

    def test_is_gsap_file_legacy(self):
        code = '''
TweenMax.to(".box", 1, { x: 100 });
'''
        assert self.parser.is_gsap_file(code, "old.js") is True

    def test_full_parse(self):
        code = '''
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const tl = gsap.timeline({ defaults: { duration: 0.5 } });
tl.to(".box", { x: 100, ease: "power2.out" })
  .to(".box", { y: 50, stagger: 0.1 });

gsap.to(".section", {
  scrollTrigger: {
    trigger: ".section",
    scrub: true,
  },
  opacity: 1,
});
'''
        result = self.parser.parse(code, "full.js")
        assert isinstance(result, GsapParseResult)
        assert result.has_tweens is True
        assert result.has_timelines is True
        assert result.has_scroll_trigger is True
        assert result.has_plugins is True
        assert len(result.detected_frameworks) >= 1
        assert len(result.detected_features) >= 1

    def test_typescript_detection(self):
        code = '''
import { gsap } from "gsap";
gsap.to(".box", { x: 100 });
'''
        result = self.parser.parse(code, "anim.ts")
        assert result.has_typescript is True

    def test_detected_features(self):
        code = '''
import { gsap } from "gsap";
gsap.to(".box", { x: 100, ease: "elastic" });
const tl = gsap.timeline();
tl.to(".box2", { y: 50, stagger: 0.1 });
'''
        result = self.parser.parse(code, "anim.js")
        assert 'tweens' in result.detected_features
        assert 'timelines' in result.detected_features


# ═══════════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestGsapScannerIntegration:
    """Tests for GSAP scanner integration."""

    def test_project_matrix_has_gsap_fields(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name="test", root_path=".")
        assert hasattr(matrix, 'gsap_tweens')
        assert hasattr(matrix, 'gsap_timelines')
        assert hasattr(matrix, 'gsap_plugins')
        assert hasattr(matrix, 'gsap_scroll_triggers')
        assert hasattr(matrix, 'gsap_imports')
        assert hasattr(matrix, 'gsap_detected_frameworks')
        assert hasattr(matrix, 'gsap_version')
        assert hasattr(matrix, 'gsap_has_typescript')
        assert hasattr(matrix, 'gsap_has_tweens')
        assert hasattr(matrix, 'gsap_has_timelines')
        assert hasattr(matrix, 'gsap_has_scroll_trigger')

    def test_scanner_has_gsap_parser(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner(".")
        assert hasattr(scanner, 'gsap_parser')
        assert isinstance(scanner.gsap_parser, EnhancedGsapParser)

    def test_parse_gsap_populates_matrix(self):
        import tempfile, os
        from pathlib import Path
        from codetrellis.scanner import ProjectScanner, ProjectMatrix

        code = '''
import { gsap } from "gsap";
gsap.to(".box", { x: 100, duration: 1, ease: "power2.out" });
const tl = gsap.timeline();
tl.to(".box", { y: 50 });
'''
        with tempfile.NamedTemporaryFile(suffix=".js", mode='w', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                scanner = ProjectScanner(".")
                matrix = ProjectMatrix(name="test", root_path=".")
                scanner._parse_gsap(Path(f.name), matrix)
                assert len(matrix.gsap_tweens) >= 1
                assert len(matrix.gsap_timelines) >= 1
                assert matrix.gsap_has_tweens is True
                assert matrix.gsap_has_timelines is True
            finally:
                os.unlink(f.name)


# ═══════════════════════════════════════════════════════════════════════
# Compressor Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestGsapCompressorIntegration:
    """Tests for GSAP compressor integration."""

    def test_compress_gsap_animations(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix

        matrix = ProjectMatrix(name="test", root_path=".")
        matrix.gsap_tweens = [
            {"name": "to", "file": "a.js", "line": 1, "has_scroll_trigger": False, "is_legacy": False},
            {"name": "from", "file": "b.js", "line": 5, "has_scroll_trigger": False, "is_legacy": False},
        ]
        matrix.gsap_eases = [
            {"name": "power2.out", "file": "a.js", "line": 1, "ease_type": "power2", "is_custom": False},
        ]

        compressor = MatrixCompressor(matrix, ".")
        lines = compressor._compress_gsap_animations(matrix)
        assert len(lines) >= 1
        assert 'tweens(2)' in lines[0]

    def test_compress_gsap_timelines(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix

        matrix = ProjectMatrix(name="test", root_path=".")
        matrix.gsap_timelines = [
            {"name": "tl", "file": "a.js", "line": 1, "method_count": 3,
             "is_legacy": False, "has_defaults": True, "has_scroll_trigger": False,
             "has_repeat": False, "has_yoyo": False},
        ]

        compressor = MatrixCompressor(matrix, ".")
        lines = compressor._compress_gsap_timelines(matrix)
        assert len(lines) >= 1
        assert 'timelines(1)' in lines[0]

    def test_compress_gsap_scroll(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix

        matrix = ProjectMatrix(name="test", root_path=".")
        matrix.gsap_scroll_triggers = [
            {"name": "create", "file": "a.js", "line": 10, "trigger": ".section",
             "has_pin": True, "has_scrub": True, "has_snap": False, "has_markers": False},
        ]

        compressor = MatrixCompressor(matrix, ".")
        lines = compressor._compress_gsap_scroll(matrix)
        assert len(lines) >= 1
        assert 'ScrollTrigger(1)' in lines[0]
        assert 'pin:1' in lines[0]

    def test_compress_gsap_api(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix

        matrix = ProjectMatrix(name="test", root_path=".")
        matrix.gsap_imports = [
            {"name": "gsap", "file": "a.js", "line": 1, "source": "gsap",
             "import_type": "esm"},
        ]
        matrix.gsap_detected_frameworks = ['gsap']
        matrix.gsap_detected_features = ['tweens', 'timelines']
        matrix.gsap_version = 'v3'
        matrix.gsap_has_typescript = True

        compressor = MatrixCompressor(matrix, ".")
        lines = compressor._compress_gsap_api(matrix)
        assert len(lines) >= 1
        assert any('imports' in l for l in lines)
        assert any('GSAP version' in l for l in lines)
        assert any('TypeScript' in l for l in lines)
