"""
Tests for Framer Motion animation framework integration.

Tests cover:
- All 5 extractors (animation, gesture, layout, scroll, api)
- Parser (EnhancedFramerMotionParser)
- Scanner integration (ProjectMatrix fields, _parse_framer_motion)
- Compressor integration ([FRAMER_*] sections)
- BPL integration (PracticeCategory enums, YAML practices)
"""

import os
import pytest
from codetrellis.extractors.framer_motion import (
    FramerAnimationExtractor,
    FramerGestureExtractor,
    FramerLayoutExtractor,
    FramerScrollExtractor,
    FramerAPIExtractor,
)
from codetrellis.framer_motion_parser_enhanced import (
    EnhancedFramerMotionParser,
    FramerMotionParseResult,
)


# ═══════════════════════════════════════════════════════════════════════
# Animation Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFramerAnimationExtractor:
    """Tests for FramerAnimationExtractor."""

    def setup_method(self):
        self.extractor = FramerAnimationExtractor()

    def test_variant_definition(self):
        code = '''
const variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['variants']) >= 1
        v = result['variants'][0]
        assert v.name == 'variants'

    def test_variant_with_transition(self):
        code = '''
const fadeIn = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.5 },
  },
};
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['variants']) >= 1

    def test_motion_component_detection(self):
        code = '''
<motion.div animate={{ opacity: 1 }} initial={{ opacity: 0 }}>
  <motion.span>Hello</motion.span>
</motion.div>
<motion.button whileHover={{ scale: 1.1 }}>Click</motion.button>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['motion_components']) >= 1

    def test_keyframe_animation(self):
        code = '''
<motion.div animate={{ x: [0, 100, 0], opacity: [0, 1, 0.5] }} />
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['keyframes']) >= 1

    def test_transition_spring(self):
        code = '''
<motion.div
  animate={{ x: 100 }}
  transition={{ type: "spring", stiffness: 200, damping: 30 }}
/>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['transitions']) >= 1

    def test_transition_tween(self):
        code = '''
<motion.div
  animate={{ opacity: 1 }}
  transition={{ type: "tween", duration: 0.5, ease: "easeOut" }}
/>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['transitions']) >= 1

    def test_animate_presence(self):
        code = '''
<AnimatePresence mode="wait" onExitComplete={handleComplete}>
  {show && <motion.div key="modal" exit={{ opacity: 0 }} />}
</AnimatePresence>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['animate_presences']) >= 1
        ap = result['animate_presences'][0]
        assert ap.mode == 'wait'

    def test_animate_presence_initial_false(self):
        code = '''
<AnimatePresence initial={false}>
  <motion.div key={selectedId} />
</AnimatePresence>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['animate_presences']) >= 1
        ap = result['animate_presences'][0]
        assert ap.has_initial is True

    def test_animation_controls_useAnimation(self):
        code = '''
const controls = useAnimation();
controls.start({ opacity: 1 });
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['animation_controls']) >= 1

    def test_animation_controls_useAnimate(self):
        code = '''
const [scope, animate] = useAnimate();
animate(scope.current, { x: 100 });
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['animation_controls']) >= 1

    def test_empty_content(self):
        result = self.extractor.extract("", "comp.tsx")
        assert result['variants'] == []
        assert result['keyframes'] == []
        assert result['transitions'] == []

    def test_whitespace_only(self):
        result = self.extractor.extract("   \n\n  ", "comp.tsx")
        assert result['variants'] == []


# ═══════════════════════════════════════════════════════════════════════
# Gesture Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFramerGestureExtractor:
    """Tests for FramerGestureExtractor."""

    def setup_method(self):
        self.extractor = FramerGestureExtractor()

    def test_drag_basic(self):
        code = '''
<motion.div drag>Drag me</motion.div>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['drags']) >= 1

    def test_drag_with_axis(self):
        code = '''
<motion.div drag="x" dragConstraints={{ left: 0, right: 300 }}>Slide</motion.div>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['drags']) >= 1

    def test_drag_with_constraints_and_elastic(self):
        code = '''
<motion.div
  drag
  dragConstraints={constraintsRef}
  dragElastic={0.2}
  dragMomentum={false}
>
  Draggable
</motion.div>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['drags']) >= 1

    def test_hover_animation(self):
        code = '''
<motion.button whileHover={{ scale: 1.1, backgroundColor: "#ff0000" }}>
  Hover me
</motion.button>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['hovers']) >= 1

    def test_tap_animation(self):
        code = '''
<motion.button whileTap={{ scale: 0.95 }}>Press me</motion.button>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['taps']) >= 1

    def test_focus_animation(self):
        code = '''
<motion.input whileFocus={{ borderColor: "#3b82f6" }} />
'''
        result = self.extractor.extract(code, "comp.tsx")
        # Focus detected in gestures
        assert len(result['gestures']) >= 1

    def test_drag_controls_hook(self):
        code = '''
const controls = useDragControls();
<motion.div
  drag="x"
  dragControls={controls}
  dragListener={false}
>
  Item
</motion.div>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['drag_controls']) >= 1

    def test_viewport_gesture(self):
        code = '''
<motion.div
  whileInView={{ opacity: 1 }}
  initial={{ opacity: 0 }}
  viewport={{ once: true, amount: 0.5 }}
/>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['gestures']) >= 1

    def test_empty_content(self):
        result = self.extractor.extract("", "comp.tsx")
        assert result['drags'] == []
        assert result['hovers'] == []

    def test_combined_gestures(self):
        code = '''
<motion.div
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
  whileDrag={{ cursor: "grabbing" }}
  drag
>
  Interactive
</motion.div>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['hovers']) >= 1
        assert len(result['taps']) >= 1
        assert len(result['drags']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Layout Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFramerLayoutExtractor:
    """Tests for FramerLayoutExtractor."""

    def setup_method(self):
        self.extractor = FramerLayoutExtractor()

    def test_layout_prop(self):
        code = '''
<motion.div layout>Content</motion.div>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['layout_anims']) >= 1

    def test_layout_position(self):
        code = '''
<motion.li layout="position">Item</motion.li>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['layout_anims']) >= 1

    def test_layout_id(self):
        code = '''
<motion.div layoutId="hero-image">
  <img src={hero} />
</motion.div>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['shared_layouts']) >= 1

    def test_shared_layout_transition(self):
        code = '''
{selected && (
  <motion.div layoutId={`card-${id}`}>
    <AnimateSharedLayout>
      <motion.h2 layoutId="title">{title}</motion.h2>
    </AnimateSharedLayout>
  </motion.div>
)}
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['shared_layouts']) >= 1

    def test_exit_animation(self):
        code = '''
<motion.div exit={{ opacity: 0, y: -20 }}>Leaving</motion.div>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['exit_anims']) >= 1

    def test_layout_group(self):
        code = '''
<LayoutGroup>
  <motion.div layout>A</motion.div>
  <motion.div layout>B</motion.div>
</LayoutGroup>
'''
        result = self.extractor.extract(code, "comp.tsx")
        # layout prop should still be detected
        assert len(result['layout_anims']) >= 1

    def test_empty_content(self):
        result = self.extractor.extract("", "comp.tsx")
        assert result['layout_anims'] == []
        assert result['shared_layouts'] == []
        assert result['exit_anims'] == []


# ═══════════════════════════════════════════════════════════════════════
# Scroll Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFramerScrollExtractor:
    """Tests for FramerScrollExtractor."""

    def setup_method(self):
        self.extractor = FramerScrollExtractor()

    def test_useScroll_basic(self):
        code = '''
const { scrollYProgress } = useScroll();
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['scrolls']) >= 1
        s = result['scrolls'][0]
        assert 'scrollYProgress' in s.scroll_values

    def test_useScroll_with_target(self):
        code = '''
const { scrollYProgress } = useScroll({
  target: containerRef,
  offset: ["start end", "end start"],
});
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['scrolls']) >= 1
        s = result['scrolls'][0]
        assert s.has_target is True
        assert s.has_offset is True

    def test_useScroll_multiple_values(self):
        code = '''
const { scrollX, scrollY, scrollXProgress, scrollYProgress } = useScroll();
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['scrolls']) >= 1
        s = result['scrolls'][0]
        assert len(s.scroll_values) >= 4

    def test_useInView_basic(self):
        code = '''
const isInView = useInView(ref);
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['in_views']) >= 1
        iv = result['in_views'][0]
        assert iv.variable_name == 'isInView'

    def test_useInView_with_options(self):
        code = '''
const isInView = useInView(ref, { once: true, amount: 0.5 });
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['in_views']) >= 1
        iv = result['in_views'][0]
        assert iv.has_once is True
        assert iv.has_amount is True

    def test_parallax_useTransform(self):
        code = '''
const y = useTransform(scrollYProgress, [0, 1], [0, -200]);
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['parallaxes']) >= 1
        px = result['parallaxes'][0]
        assert px.variable_name == 'y'
        assert px.input_source == 'scrollYProgress'

    def test_parallax_opacity(self):
        code = '''
const opacity = useTransform(scrollYProgress, [0, 0.5, 1], [0, 1, 0]);
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['parallaxes']) >= 1
        px = result['parallaxes'][0]
        assert px.output_property == 'opacity'

    def test_scroll_event(self):
        code = '''
useMotionValueEvent(scrollY, "change", (latest) => {
  console.log(latest);
});
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['scroll_events']) >= 1

    def test_empty_content(self):
        result = self.extractor.extract("", "comp.tsx")
        assert result['scrolls'] == []
        assert result['in_views'] == []
        assert result['parallaxes'] == []


# ═══════════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFramerAPIExtractor:
    """Tests for FramerAPIExtractor."""

    def setup_method(self):
        self.extractor = FramerAPIExtractor()

    def test_named_import_framer_motion(self):
        code = '''
import { motion, AnimatePresence } from 'framer-motion';
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.package_name == 'framer-motion'
        assert 'motion' in imp.imported_names
        assert 'AnimatePresence' in imp.imported_names

    def test_named_import_motion_package(self):
        code = '''
import { motion, useAnimate } from 'motion';
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.package_name == 'motion'

    def test_dynamic_import(self):
        code = '''
const { motion } = await import('framer-motion');
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['imports']) >= 1
        assert result['imports'][0].is_dynamic is True

    def test_hook_useMotionValue(self):
        code = '''
const x = useMotionValue(0);
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['hooks']) >= 1
        hk = result['hooks'][0]
        assert hk.hook_name == 'useMotionValue'
        assert hk.variable_name == 'x'

    def test_hook_useTransform(self):
        code = '''
const opacity = useTransform(x, [0, 100], [1, 0]);
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['hooks']) >= 1

    def test_hook_useSpring(self):
        code = '''
const smoothX = useSpring(x, { stiffness: 100, damping: 30 });
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['hooks']) >= 1
        hk = result['hooks'][0]
        assert hk.hook_name == 'useSpring'

    def test_hook_useAnimate(self):
        code = '''
const [scope, animate] = useAnimate();
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['hooks']) >= 1

    def test_hook_useReducedMotion(self):
        code = '''
const prefersReduced = useReducedMotion();
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['hooks']) >= 1
        hk = result['hooks'][0]
        assert hk.hook_name == 'useReducedMotion'

    def test_typescript_types(self):
        code = '''
const variants: Variants = { hidden: { opacity: 0 } };
const transition: Transition = { type: "spring" };
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['types']) >= 1

    def test_motion_elements(self):
        code = '''
<motion.div>Div</motion.div>
<motion.span>Span</motion.span>
<motion.button>Button</motion.button>
<motion.div>Another div</motion.div>
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['motion_elements']) >= 1
        # Check div is counted
        div_elem = next((e for e in result['motion_elements'] if e['element'] == 'motion.div'), None)
        assert div_elem is not None
        assert div_elem['count'] >= 2

    def test_motion_factory(self):
        code = '''
const MotionCard = motion(Card);
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['motion_elements']) >= 1
        elem = result['motion_elements'][-1]
        assert 'motion(Card)' in elem['element']

    def test_react_spring_integration(self):
        code = '''
import { useSpring } from '@react-spring/framer-motion';
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['integrations']) >= 1
        integ = result['integrations'][0]
        assert integ.library_name == 'react-spring'

    def test_popmotion_integration(self):
        code = '''
import { animate } from 'popmotion';
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['integrations']) >= 1
        integ = result['integrations'][0]
        assert integ.library_name == 'popmotion'

    def test_version_detection_framer_motion(self):
        code = '''
import { motion, useAnimate, useScroll, useInView } from 'framer-motion';
'''
        result = self.extractor.extract(code, "comp.tsx")
        vi = result['version_info']
        assert vi['package'] == 'framer-motion'
        assert any('useAnimate' in h for h in vi['api_hints'])

    def test_version_detection_motion_v11(self):
        code = '''
import { motion, useAnimationFrame } from 'motion';
'''
        result = self.extractor.extract(code, "comp.tsx")
        vi = result['version_info']
        assert vi['package'] == 'motion'
        assert any('v11' in h for h in vi['api_hints'])

    def test_empty_content(self):
        result = self.extractor.extract("", "comp.tsx")
        assert result['imports'] == []
        assert result['hooks'] == []
        assert result['types'] == []

    def test_import_with_alias(self):
        code = '''
import { motion as m, AnimatePresence as AP } from 'framer-motion';
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert 'motion' in imp.imported_names

    def test_subpath_import(self):
        code = '''
import { domAnimation } from 'framer-motion/dom';
'''
        result = self.extractor.extract(code, "comp.tsx")
        assert len(result['imports']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Enhanced Parser Tests
# ═══════════════════════════════════════════════════════════════════════

class TestEnhancedFramerMotionParser:
    """Tests for EnhancedFramerMotionParser."""

    def setup_method(self):
        self.parser = EnhancedFramerMotionParser()

    def test_parse_result_type(self):
        result = self.parser.parse("", "comp.tsx")
        assert isinstance(result, FramerMotionParseResult)

    def test_file_type_detection_tsx(self):
        result = self.parser.parse("", "comp.tsx")
        assert result.file_type == 'tsx'
        assert result.has_typescript is True

    def test_file_type_detection_ts(self):
        result = self.parser.parse("", "utils.ts")
        assert result.file_type == 'ts'
        assert result.has_typescript is True

    def test_file_type_detection_jsx(self):
        result = self.parser.parse("", "comp.jsx")
        assert result.file_type == 'jsx'
        assert result.has_typescript is False

    def test_file_type_detection_js(self):
        result = self.parser.parse("", "comp.js")
        assert result.file_type == 'js'

    def test_comprehensive_parse(self):
        code = '''
import { motion, AnimatePresence, useScroll, useTransform, useMotionValue } from 'framer-motion';

const variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { staggerChildren: 0.1 },
  },
};

function AnimatedPage() {
  const { scrollYProgress } = useScroll();
  const opacity = useTransform(scrollYProgress, [0, 1], [1, 0]);
  const x = useMotionValue(0);

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key="page"
        variants={variants}
        initial="hidden"
        animate="visible"
        exit={{ opacity: 0 }}
        layout
        layoutId="page"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        drag="x"
        dragConstraints={{ left: 0, right: 200 }}
        transition={{ type: "spring", stiffness: 300 }}
      >
        <motion.h1
          whileInView={{ opacity: 1 }}
          initial={{ opacity: 0 }}
          viewport={{ once: true }}
        >
          Hello
        </motion.h1>
      </motion.div>
    </AnimatePresence>
  );
}
'''
        result = self.parser.parse(code, "AnimatedPage.tsx")

        # Verify all extractors ran
        assert result.file_type == 'tsx'
        assert result.has_typescript is True
        assert len(result.imports) >= 1
        assert len(result.variants) >= 1
        assert len(result.animate_presences) >= 1
        assert len(result.scrolls) >= 1
        assert len(result.parallaxes) >= 1
        assert len(result.hooks) >= 1
        assert result.has_variants is True
        assert result.has_animate_presence is True
        assert result.has_scroll_animations is True

    def test_is_framer_motion_file_import(self):
        assert self.parser.is_framer_motion_file("import { motion } from 'framer-motion';") is True

    def test_is_framer_motion_file_motion_import(self):
        assert self.parser.is_framer_motion_file("import { motion } from 'motion';") is True

    def test_is_framer_motion_file_jsx(self):
        assert self.parser.is_framer_motion_file("<motion.div animate={{ opacity: 1 }} />") is True

    def test_is_framer_motion_file_animate_presence(self):
        assert self.parser.is_framer_motion_file("<AnimatePresence>") is True

    def test_is_framer_motion_file_hooks(self):
        assert self.parser.is_framer_motion_file("const x = useMotionValue(0);") is True

    def test_is_framer_motion_file_while_hover(self):
        assert self.parser.is_framer_motion_file('whileHover={{ scale: 1.1 }}') is True

    def test_is_framer_motion_file_false(self):
        assert self.parser.is_framer_motion_file("const x = 42;") is False

    def test_is_framer_motion_file_dynamic_import(self):
        assert self.parser.is_framer_motion_file("const m = await import('framer-motion');") is True

    def test_is_framer_motion_file_lazy_motion(self):
        assert self.parser.is_framer_motion_file("<LazyMotion features={domAnimation}>") is True

    def test_is_framer_motion_file_reorder(self):
        assert self.parser.is_framer_motion_file("<Reorder.Group axis='y'>") is True

    def test_detect_frameworks_framer_motion(self):
        code = "import { motion } from 'framer-motion';"
        result = self.parser._detect_frameworks(code)
        assert 'framer-motion' in result

    def test_detect_frameworks_motion_v11(self):
        code = "import { motion } from 'motion';"
        result = self.parser._detect_frameworks(code)
        assert 'motion' in result

    def test_detect_frameworks_popmotion(self):
        code = "import { animate } from 'popmotion';"
        result = self.parser._detect_frameworks(code)
        assert 'popmotion' in result

    def test_detected_features(self):
        code = '''
import { motion, AnimatePresence, useScroll } from 'framer-motion';
const variants = { hidden: { opacity: 0 }, visible: { opacity: 1 } };
<motion.div drag whileHover={{ scale: 1.1 }} layout exit={{ opacity: 0 }}>
  <AnimatePresence />
</motion.div>
const { scrollYProgress } = useScroll();
'''
        result = self.parser.parse(code, "comp.tsx")
        assert 'variants' in result.detected_features
        assert 'motion_components' in result.detected_features

    def test_version_framer_motion(self):
        code = "import { motion } from 'framer-motion';"
        result = self.parser.parse(code, "comp.tsx")
        assert result.framer_motion_version == 'v1-v10'

    def test_version_motion_v11(self):
        code = "import { motion } from 'motion';"
        result = self.parser.parse(code, "comp.tsx")
        assert result.framer_motion_version == 'v11+'


# ═══════════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFramerMotionScannerIntegration:
    """Tests for scanner.py ProjectMatrix framer_motion_* fields."""

    def test_project_matrix_has_framer_motion_fields(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')

        # Verify all framer_motion_* fields exist
        assert hasattr(matrix, 'framer_motion_variants')
        assert hasattr(matrix, 'framer_motion_keyframes')
        assert hasattr(matrix, 'framer_motion_transitions')
        assert hasattr(matrix, 'framer_motion_animate_presences')
        assert hasattr(matrix, 'framer_motion_animation_controls')
        assert hasattr(matrix, 'framer_motion_motion_components')
        assert hasattr(matrix, 'framer_motion_drags')
        assert hasattr(matrix, 'framer_motion_hovers')
        assert hasattr(matrix, 'framer_motion_taps')
        assert hasattr(matrix, 'framer_motion_gestures')
        assert hasattr(matrix, 'framer_motion_layout_anims')
        assert hasattr(matrix, 'framer_motion_shared_layouts')
        assert hasattr(matrix, 'framer_motion_exit_anims')
        assert hasattr(matrix, 'framer_motion_scrolls')
        assert hasattr(matrix, 'framer_motion_in_views')
        assert hasattr(matrix, 'framer_motion_parallaxes')
        assert hasattr(matrix, 'framer_motion_imports')
        assert hasattr(matrix, 'framer_motion_hooks')
        assert hasattr(matrix, 'framer_motion_types')
        assert hasattr(matrix, 'framer_motion_integrations')
        assert hasattr(matrix, 'framer_motion_motion_elements')
        assert hasattr(matrix, 'framer_motion_detected_frameworks')
        assert hasattr(matrix, 'framer_motion_detected_features')
        assert hasattr(matrix, 'framer_motion_version')
        assert hasattr(matrix, 'framer_motion_has_typescript')
        assert hasattr(matrix, 'framer_motion_has_variants')
        assert hasattr(matrix, 'framer_motion_has_gestures')
        assert hasattr(matrix, 'framer_motion_has_layout_animations')
        assert hasattr(matrix, 'framer_motion_has_scroll_animations')
        assert hasattr(matrix, 'framer_motion_has_animate_presence')
        assert hasattr(matrix, 'framer_motion_has_drag')

    def test_project_matrix_fields_default_empty(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')

        assert matrix.framer_motion_variants == []
        assert matrix.framer_motion_keyframes == []
        assert matrix.framer_motion_transitions == []
        assert matrix.framer_motion_drags == []
        assert matrix.framer_motion_imports == []
        assert matrix.framer_motion_hooks == []
        assert matrix.framer_motion_version == ""
        assert matrix.framer_motion_has_typescript is False
        assert matrix.framer_motion_has_variants is False

    def test_scanner_has_framer_motion_parser(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        assert hasattr(scanner, 'framer_motion_parser')
        assert isinstance(scanner.framer_motion_parser, EnhancedFramerMotionParser)

    def test_scanner_has_parse_framer_motion_method(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        assert hasattr(scanner, '_parse_framer_motion')
        assert callable(scanner._parse_framer_motion)


# ═══════════════════════════════════════════════════════════════════════
# Compressor Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFramerMotionCompressorIntegration:
    """Tests for compressor.py [FRAMER_*] sections."""

    def test_compressor_has_framer_methods(self):
        from codetrellis.compressor import MatrixCompressor
        comp = MatrixCompressor()
        assert hasattr(comp, '_compress_framer_motion_animations')
        assert hasattr(comp, '_compress_framer_motion_gestures')
        assert hasattr(comp, '_compress_framer_motion_layout')
        assert hasattr(comp, '_compress_framer_motion_scroll')
        assert hasattr(comp, '_compress_framer_motion_api')

    def test_compress_animations_empty(self):
        from codetrellis.scanner import ProjectMatrix
        from codetrellis.compressor import MatrixCompressor
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        comp = MatrixCompressor()
        result = comp._compress_framer_motion_animations(matrix)
        assert result == []

    def test_compress_animations_with_data(self):
        from codetrellis.scanner import ProjectMatrix
        from codetrellis.compressor import MatrixCompressor
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.framer_motion_variants = [
            {"name": "fadeIn", "file": "comp.tsx", "line": 5, "states": ["hidden", "visible"], "has_transition": True},
            {"name": "slideUp", "file": "comp.tsx", "line": 15, "states": ["initial", "animate"], "has_transition": False},
        ]
        comp = MatrixCompressor()
        result = comp._compress_framer_motion_animations(matrix)
        assert len(result) >= 1
        assert any('variants' in line for line in result)

    def test_compress_gestures_with_data(self):
        from codetrellis.scanner import ProjectMatrix
        from codetrellis.compressor import MatrixCompressor
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.framer_motion_drags = [
            {"name": "motion.div", "file": "comp.tsx", "line": 10, "has_constraints": True, "has_elastic": False, "has_momentum": False, "axis": "x"},
        ]
        comp = MatrixCompressor()
        result = comp._compress_framer_motion_gestures(matrix)
        assert len(result) >= 1
        assert any('drag' in line for line in result)

    def test_compress_layout_with_data(self):
        from codetrellis.scanner import ProjectMatrix
        from codetrellis.compressor import MatrixCompressor
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.framer_motion_layout_anims = [
            {"name": "motion.div", "file": "comp.tsx", "line": 5, "layout_type": "layout", "has_layout_id": True},
        ]
        comp = MatrixCompressor()
        result = comp._compress_framer_motion_layout(matrix)
        assert len(result) >= 1
        assert any('layout' in line for line in result)

    def test_compress_scroll_with_data(self):
        from codetrellis.scanner import ProjectMatrix
        from codetrellis.compressor import MatrixCompressor
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.framer_motion_scrolls = [
            {"name": "scrollYProgress", "file": "comp.tsx", "line": 5, "scroll_values": ["scrollYProgress"], "has_target": True, "has_offset": True},
        ]
        comp = MatrixCompressor()
        result = comp._compress_framer_motion_scroll(matrix)
        assert len(result) >= 1
        assert any('useScroll' in line for line in result)

    def test_compress_api_with_data(self):
        from codetrellis.scanner import ProjectMatrix
        from codetrellis.compressor import MatrixCompressor
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.framer_motion_imports = [
            {"name": "motion, AnimatePresence", "file": "comp.tsx", "line": 1, "package": "framer-motion", "is_dynamic": False},
        ]
        matrix.framer_motion_hooks = [
            {"name": "useMotionValue", "file": "comp.tsx", "line": 5, "variable": "x"},
        ]
        matrix.framer_motion_detected_frameworks = ['framer-motion']
        matrix.framer_motion_detected_features = ['variants', 'gestures']
        matrix.framer_motion_version = 'v1-v10'
        comp = MatrixCompressor()
        result = comp._compress_framer_motion_api(matrix)
        assert len(result) >= 1
        assert any('framer-motion' in line for line in result)

    def test_full_compress_includes_framer_sections(self):
        from codetrellis.scanner import ProjectMatrix
        from codetrellis.compressor import MatrixCompressor
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.framer_motion_variants = [
            {"name": "fadeIn", "file": "comp.tsx", "line": 5, "states": ["hidden", "visible"], "has_transition": True},
        ]
        matrix.framer_motion_imports = [
            {"name": "motion", "file": "comp.tsx", "line": 1, "package": "framer-motion", "is_dynamic": False},
        ]
        comp = MatrixCompressor()
        result = comp.compress(matrix)
        assert '[FRAMER_ANIMATIONS]' in result
        assert '[FRAMER_API]' in result


# ═══════════════════════════════════════════════════════════════════════
# BPL Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFramerMotionBPLIntegration:
    """Tests for BPL models, selector, and practices YAML."""

    def test_practice_category_enums_exist(self):
        from codetrellis.bpl.models import PracticeCategory
        assert PracticeCategory.FRAMER_ANIMATIONS.value == "framer_animations"
        assert PracticeCategory.FRAMER_VARIANTS.value == "framer_variants"
        assert PracticeCategory.FRAMER_GESTURES.value == "framer_gestures"
        assert PracticeCategory.FRAMER_LAYOUT.value == "framer_layout"
        assert PracticeCategory.FRAMER_SCROLL.value == "framer_scroll"
        assert PracticeCategory.FRAMER_TRANSITIONS.value == "framer_transitions"
        assert PracticeCategory.FRAMER_PERFORMANCE.value == "framer_performance"
        assert PracticeCategory.FRAMER_ACCESSIBILITY.value == "framer_accessibility"
        assert PracticeCategory.FRAMER_HOOKS.value == "framer_hooks"
        assert PracticeCategory.FRAMER_ECOSYSTEM.value == "framer_ecosystem"

    def test_yaml_practices_file_exists(self):
        """Verify the YAML practices file exists and is parseable."""
        import yaml
        # Navigate from tests/unit/ to repo root
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        yaml_path = os.path.join(
            repo_root, 'codetrellis', 'bpl', 'practices', 'framer_motion_core.yaml'
        )
        assert os.path.exists(yaml_path), f"YAML file not found: {yaml_path}"

        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        assert 'practices' in data
        practices = data['practices']
        assert len(practices) == 50, f"Expected 50 practices, got {len(practices)}"

    def test_yaml_practice_ids_sequential(self):
        """Verify practice IDs are FRAMER001-FRAMER050."""
        import yaml
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        yaml_path = os.path.join(
            repo_root, 'codetrellis', 'bpl', 'practices', 'framer_motion_core.yaml'
        )
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        practices = data['practices']
        for i, p in enumerate(practices, 1):
            expected_id = f"FRAMER{i:03d}"
            assert p['id'] == expected_id, f"Expected {expected_id}, got {p['id']}"

    def test_yaml_practice_categories_valid(self):
        """Verify all practice categories match PracticeCategory enum values."""
        import yaml
        from codetrellis.bpl.models import PracticeCategory
        valid_cats = {c.value for c in PracticeCategory}
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        yaml_path = os.path.join(
            repo_root, 'codetrellis', 'bpl', 'practices', 'framer_motion_core.yaml'
        )
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        for p in data['practices']:
            assert p['category'] in valid_cats, f"Invalid category '{p['category']}' for {p['id']}"

    def test_yaml_practice_distribution(self):
        """Verify practices are distributed across all 10 categories (5 each)."""
        import yaml
        from collections import Counter
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        yaml_path = os.path.join(
            repo_root, 'codetrellis', 'bpl', 'practices', 'framer_motion_core.yaml'
        )
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        counts = Counter(p['category'] for p in data['practices'])
        expected_cats = [
            'framer_animations', 'framer_variants', 'framer_gestures',
            'framer_layout', 'framer_scroll', 'framer_transitions',
            'framer_performance', 'framer_accessibility', 'framer_hooks',
            'framer_ecosystem',
        ]
        for cat in expected_cats:
            assert counts[cat] == 5, f"Expected 5 practices for {cat}, got {counts.get(cat, 0)}"

    def test_yaml_practice_required_fields(self):
        """Verify each practice has required fields."""
        import yaml
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        yaml_path = os.path.join(
            repo_root, 'codetrellis', 'bpl', 'practices', 'framer_motion_core.yaml'
        )
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        required = ['id', 'title', 'description', 'category', 'level', 'frameworks', 'tags']
        for p in data['practices']:
            for field in required:
                assert field in p, f"Missing field '{field}' in practice {p.get('id', '?')}"


# ═══════════════════════════════════════════════════════════════════════
# Edge Case & Comprehensive Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFramerMotionEdgeCases:
    """Edge case tests across all extractors."""

    def setup_method(self):
        self.parser = EnhancedFramerMotionParser()

    def test_minified_code(self):
        code = '''import{motion as m,AnimatePresence}from'framer-motion';const v={hidden:{opacity:0},visible:{opacity:1}};'''
        # Should not crash
        result = self.parser.parse(code, "min.js")
        assert isinstance(result, FramerMotionParseResult)

    def test_require_syntax(self):
        code = '''
const { motion, AnimatePresence } = require('framer-motion');
'''
        assert self.parser.is_framer_motion_file(code) is True

    def test_very_large_file(self):
        code = "import { motion } from 'framer-motion';\n" * 100
        code += "<motion.div animate={{ opacity: 1 }} />\n" * 50
        result = self.parser.parse(code, "large.tsx")
        assert isinstance(result, FramerMotionParseResult)
        assert len(result.imports) >= 1

    def test_no_framer_motion_code(self):
        code = '''
import React from 'react';
const App = () => <div>Hello</div>;
'''
        assert self.parser.is_framer_motion_file(code) is False

    def test_framer_motion_3d(self):
        code = "import { motion } from 'framer-motion-3d';"
        assert self.parser.is_framer_motion_file(code) is True

    def test_framer_sdk(self):
        code = "import { motion } from 'framer';"
        assert self.parser.is_framer_motion_file(code) is True

    def test_multiple_components_same_file(self):
        code = '''
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';

const { scrollYProgress } = useScroll();
const y = useTransform(scrollYProgress, [0, 1], [0, -100]);

const Card = () => (
  <motion.div
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
    layout
    layoutId="card"
    drag="x"
    dragConstraints={{ left: 0, right: 200 }}
    exit={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ type: "spring" }}
  />
);

const Modal = () => (
  <AnimatePresence>
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    />
  </AnimatePresence>
);
'''
        result = self.parser.parse(code, "components.tsx")
        assert result.has_variants is True  # Inline animate={{ opacity: 1 }} detected as variants
        assert result.has_drag is True
        assert result.has_animate_presence is True
        assert result.has_scroll_animations is True
        assert result.has_layout_animations is True

    def test_useScroll_with_container(self):
        code = '''
const { scrollYProgress } = useScroll({
  container: scrollRef,
});
'''
        extractor = FramerScrollExtractor()
        result = extractor.extract(code, "comp.tsx")
        assert len(result['scrolls']) >= 1
        assert result['scrolls'][0].has_container is True

    def test_multiple_hooks_same_file(self):
        code = '''
const x = useMotionValue(0);
const smoothX = useSpring(x);
const opacity = useTransform(x, [0, 100], [1, 0]);
const velocity = useVelocity(x);
'''
        extractor = FramerAPIExtractor()
        result = extractor.extract(code, "comp.tsx")
        assert len(result['hooks']) >= 3

    def test_reorder_detection(self):
        code = '<Reorder.Group axis="y" values={items}><Reorder.Item key={item} value={item} /></Reorder.Group>'
        assert self.parser.is_framer_motion_file(code) is True

    def test_while_drag_detection(self):
        code = 'whileDrag={{ scale: 1.1 }}'
        assert self.parser.is_framer_motion_file(code) is True
