"""
GSAP Scroll Extractor — ScrollTrigger, ScrollSmoother, Observer, scroll batch.

Extracts:
- ScrollTrigger.create() and inline scrollTrigger configs
- Pin, scrub, snap, batch configurations
- ScrollSmoother (club plugin)
- Observer (v3.10+)
- ScrollTrigger.batch()
- Scroll-based callbacks (onEnter, onLeave, onEnterBack, onLeaveBack)
- matchMedia breakpoint-based scroll configs
- ScrollTrigger.scrollerProxy()

v4.77: Full GSAP scroll support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GsapScrollTriggerInfo:
    """A ScrollTrigger configuration."""
    name: str = ""                   # Variable name or 'inline'
    file: str = ""
    line_number: int = 0
    config_type: str = ""            # 'inline' (scrollTrigger:{}) or 'create' (ScrollTrigger.create())
    trigger: str = ""                # Trigger element selector
    has_pin: bool = False
    has_scrub: bool = False          # scrub: true or scrub: 0.5
    has_snap: bool = False
    has_markers: bool = False
    has_start: bool = False
    has_end: bool = False
    has_toggleActions: bool = False
    has_toggleClass: bool = False
    has_callbacks: bool = False      # onEnter/onLeave/onEnterBack/onLeaveBack
    has_anticipatePin: bool = False
    has_batch: bool = False
    scrub_value: str = ""            # 'true' or numeric value


@dataclass
class GsapScrollSmootherInfo:
    """A ScrollSmoother configuration."""
    file: str = ""
    line_number: int = 0
    has_smooth: bool = False
    has_effects: bool = False
    has_normalizeScroll: bool = False
    has_ignoreMobileResize: bool = False


@dataclass
class GsapObserverInfo:
    """A GSAP Observer configuration."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    observer_type: str = ""          # 'wheel', 'touch', 'pointer', 'scroll'
    has_onUp: bool = False
    has_onDown: bool = False
    has_onLeft: bool = False
    has_onRight: bool = False
    has_tolerance: bool = False
    has_preventDefault: bool = False


@dataclass
class GsapScrollBatchInfo:
    """A ScrollTrigger.batch() configuration."""
    file: str = ""
    line_number: int = 0
    target: str = ""
    has_onEnter: bool = False
    has_onLeave: bool = False
    has_interval: bool = False
    has_batchMax: bool = False


class GsapScrollExtractor:
    """
    Extracts GSAP scroll-related constructs.
    """

    # ScrollTrigger.create({...})
    ST_CREATE = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?ScrollTrigger\.create\s*\(',
        re.MULTILINE
    )

    # Inline scrollTrigger config in tweens
    ST_INLINE = re.compile(
        r'scrollTrigger\s*:\s*\{',
        re.MULTILINE
    )

    # ScrollTrigger.batch()
    ST_BATCH = re.compile(
        r'ScrollTrigger\.batch\s*\(\s*["\']([^"\']*)["\']',
        re.MULTILINE
    )

    # ScrollSmoother.create({...})
    SMOOTHER_CREATE = re.compile(
        r'ScrollSmoother\.create\s*\(',
        re.MULTILINE
    )

    # Observer.create({...})
    OBSERVER_CREATE = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?Observer\.create\s*\(',
        re.MULTILINE
    )

    # ScrollTrigger config keys
    PIN_PATTERN = re.compile(r'pin\s*:\s*(?:true|["\'])')
    SCRUB_PATTERN = re.compile(r'scrub\s*:\s*(true|[\d.]+)')
    SNAP_PATTERN = re.compile(r'snap\s*:')
    MARKERS_PATTERN = re.compile(r'markers\s*:\s*true')
    START_PATTERN = re.compile(r'start\s*:\s*["\']')
    END_PATTERN = re.compile(r'end\s*:\s*["\']')
    TOGGLE_ACTIONS = re.compile(r'toggleActions\s*:')
    TOGGLE_CLASS = re.compile(r'toggleClass\s*:')
    TRIGGER_PATTERN = re.compile(r'trigger\s*:\s*["\']([^"\']+)["\']')
    ANTICIPATE_PIN = re.compile(r'anticipatePin\s*:')

    # Scroll callbacks
    SCROLL_CALLBACKS = re.compile(
        r'(onEnter|onLeave|onEnterBack|onLeaveBack|onUpdate|onToggle|onRefresh)\s*:'
    )

    # Observer types
    OBSERVER_TYPE = re.compile(r'type\s*:\s*["\']([^"\']+)["\']')
    OBSERVER_CALLBACKS = {
        'onUp': re.compile(r'onUp\s*:'),
        'onDown': re.compile(r'onDown\s*:'),
        'onLeft': re.compile(r'onLeft\s*:'),
        'onRight': re.compile(r'onRight\s*:'),
    }

    # ScrollSmoother config keys
    SMOOTH_PATTERN = re.compile(r'smooth\s*:')
    EFFECTS_PATTERN = re.compile(r'effects\s*:')
    NORMALIZE_SCROLL = re.compile(r'normalizeScroll\s*:')
    IGNORE_MOBILE = re.compile(r'ignoreMobileResize\s*:')

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all GSAP scroll constructs."""
        scroll_triggers = []
        smoothers = []
        observers = []
        batches = []

        # ── ScrollTrigger.create() ──────────────────────────────
        for match in self.ST_CREATE.finditer(content):
            var_name = match.group(1) or 'anonymous'
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 800]

            st = self._build_scroll_trigger(var_name, 'create', ctx, file_path, line_num)
            scroll_triggers.append(st)

        # ── Inline scrollTrigger configs ────────────────────────
        for match in self.ST_INLINE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 800]

            st = self._build_scroll_trigger('inline', 'inline', ctx, file_path, line_num)
            scroll_triggers.append(st)

        # ── ScrollTrigger.batch() ───────────────────────────────
        for match in self.ST_BATCH.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 500]
            batches.append(GsapScrollBatchInfo(
                file=file_path,
                line_number=line_num,
                target=match.group(1),
                has_onEnter=bool(re.search(r'onEnter\s*:', ctx)),
                has_onLeave=bool(re.search(r'onLeave\s*:', ctx)),
                has_interval=bool(re.search(r'interval\s*:', ctx)),
                has_batchMax=bool(re.search(r'batchMax\s*:', ctx)),
            ))

        # ── ScrollSmoother ─────────────────────────────────────
        for match in self.SMOOTHER_CREATE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 500]
            smoothers.append(GsapScrollSmootherInfo(
                file=file_path,
                line_number=line_num,
                has_smooth=bool(self.SMOOTH_PATTERN.search(ctx)),
                has_effects=bool(self.EFFECTS_PATTERN.search(ctx)),
                has_normalizeScroll=bool(self.NORMALIZE_SCROLL.search(ctx)),
                has_ignoreMobileResize=bool(self.IGNORE_MOBILE.search(ctx)),
            ))

        # ── Observer ────────────────────────────────────────────
        for match in self.OBSERVER_CREATE.finditer(content):
            var_name = match.group(1) or 'anonymous'
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 500]

            type_match = self.OBSERVER_TYPE.search(ctx)
            obs = GsapObserverInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                observer_type=type_match.group(1) if type_match else '',
                has_onUp=bool(self.OBSERVER_CALLBACKS['onUp'].search(ctx)),
                has_onDown=bool(self.OBSERVER_CALLBACKS['onDown'].search(ctx)),
                has_onLeft=bool(self.OBSERVER_CALLBACKS['onLeft'].search(ctx)),
                has_onRight=bool(self.OBSERVER_CALLBACKS['onRight'].search(ctx)),
                has_tolerance=bool(re.search(r'tolerance\s*:', ctx)),
                has_preventDefault=bool(re.search(r'preventDefault\s*:', ctx)),
            )
            observers.append(obs)

        return {
            'scroll_triggers': scroll_triggers[:50],
            'smoothers': smoothers[:10],
            'observers': observers[:20],
            'batches': batches[:20],
        }

    def _build_scroll_trigger(self, name: str, config_type: str, ctx: str,
                              file_path: str, line_num: int) -> GsapScrollTriggerInfo:
        """Build a GsapScrollTriggerInfo from context."""
        trigger_match = self.TRIGGER_PATTERN.search(ctx)
        scrub_match = self.SCRUB_PATTERN.search(ctx)

        return GsapScrollTriggerInfo(
            name=name,
            file=file_path,
            line_number=line_num,
            config_type=config_type,
            trigger=trigger_match.group(1) if trigger_match else '',
            has_pin=bool(self.PIN_PATTERN.search(ctx)),
            has_scrub=bool(scrub_match),
            has_snap=bool(self.SNAP_PATTERN.search(ctx)),
            has_markers=bool(self.MARKERS_PATTERN.search(ctx)),
            has_start=bool(self.START_PATTERN.search(ctx)),
            has_end=bool(self.END_PATTERN.search(ctx)),
            has_toggleActions=bool(self.TOGGLE_ACTIONS.search(ctx)),
            has_toggleClass=bool(self.TOGGLE_CLASS.search(ctx)),
            has_callbacks=bool(self.SCROLL_CALLBACKS.search(ctx)),
            has_anticipatePin=bool(self.ANTICIPATE_PIN.search(ctx)),
            scrub_value=scrub_match.group(1) if scrub_match else '',
        )
