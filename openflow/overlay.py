"""
Overlay bar for OpenFlow.

This module implements a custom NSPanel that:
- Appears on the active monitor when recording starts.
- Displays voice-reactive wave bars.
- Shows processing and completion states with animations.
"""

from AppKit import (
    NSPanel, NSColor, NSScreen, NSView, NSEvent,
    NSBorderlessWindowMask, NSWindowStyleMaskNonactivatingPanel,
    NSBackingStoreBuffered, NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSAnimationContext,
)
from Quartz import (
    CABasicAnimation, CAMediaTimingFunction, CAShapeLayer,
    CATransaction, CGRectMake, CGPathCreateMutable,
    CGPathMoveToPoint, CGPathAddLineToPoint, CGPathAddArc,
    CACurrentMediaTime,
)
import objc
import math
import threading
import logging
from PyObjCTools import AppHelper

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _rect(frame):
    """Extract (x, y, w, h) from an NSRect or a plain Python tuple."""
    try:
        return (frame.origin.x, frame.origin.y,
                frame.size.width, frame.size.height)
    except AttributeError:
        return (frame[0][0], frame[0][1], frame[1][0], frame[1][1])


def _nscolor(r, g, b, a=1.0):
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)


# ─── Constants ────────────────────────────────────────────────────────────────
PILL_WIDTH       = 180
PILL_HEIGHT      = 38
PILL_RADIUS      = PILL_HEIGHT / 2.0
BOTTOM_MARGIN    = 60
SLIDE_DURATION   = 0.28
DONE_VISIBLE_SECS = 0.7

# Colors
CLR_BG_DARK      = (0.10, 0.10, 0.12, 0.92)
CLR_PROCESSING   = (0.14, 0.14, 0.16, 0.94)
CLR_DONE         = (0.14, 0.75, 0.45, 0.94)

# Wave bar config
NUM_WAVE_BARS    = 5
WAVE_BAR_WIDTH   = 3.0
WAVE_BAR_GAP     = 4.5
WAVE_BAR_MIN_H   = 3.0
WAVE_BAR_MAX_H   = 20.0
WAVE_BAR_RADIUS  = 1.5
WAVE_BAR_COLOR   = (1.0, 1.0, 1.0, 0.85)


# ─── Panel subclass ──────────────────────────────────────────────────────────
class OverlayPanel(NSPanel):
    def canBecomeKeyWindow(self):
        return False

    def canBecomeMainWindow(self):
        return False


# ─── FlowBarView ──────────────────────────────────────────────────────────────
class FlowBarView(NSView):
    """Draws the pill and hosts wave bars, spinner, and checkmark sublayers."""

    def initWithFrame_(self, frame):
        self = objc.super(FlowBarView, self).initWithFrame_(frame)
        if self is None:
            return None

        self.setWantsLayer_(True)
        root = self.layer()
        root.setCornerRadius_(PILL_RADIUS)
        root.setMasksToBounds_(True)
        root.setBackgroundColor_(_nscolor(*CLR_BG_DARK).CGColor())

        _, _, fw, fh = _rect(frame)

        # ── Wave bars (voice-reactive) ────────────────────────────────
        self._wave_layers = []
        total_w = NUM_WAVE_BARS * WAVE_BAR_WIDTH + (NUM_WAVE_BARS - 1) * WAVE_BAR_GAP
        start_x = (fw - total_w) / 2.0
        self._pill_h = fh

        for i in range(NUM_WAVE_BARS):
            bar = CAShapeLayer.alloc().init()
            bx = start_x + i * (WAVE_BAR_WIDTH + WAVE_BAR_GAP)
            by = (fh - WAVE_BAR_MIN_H) / 2.0
            bar.setFrame_(CGRectMake(bx, by, WAVE_BAR_WIDTH, WAVE_BAR_MIN_H))
            bar.setCornerRadius_(WAVE_BAR_RADIUS)
            bar.setBackgroundColor_(_nscolor(*WAVE_BAR_COLOR).CGColor())
            bar.setOpacity_(0.0)
            root.addSublayer_(bar)
            self._wave_layers.append(bar)

        self._waves_visible = False
        self._current_levels = [0.0] * NUM_WAVE_BARS  # running level per bar
        self._spinner_layer = None
        self._check_layers = []
        self._dot_layers = []

        return self

    # ── Background colour transition ──────────────────────────────────────────
    def setBackgroundColor_animated_(self, color, animated=True):
        layer = self.layer()
        if not layer:
            return
        if not animated:
            layer.setBackgroundColor_(color.CGColor())
            return
        try:
            anim = CABasicAnimation.animationWithKeyPath_("backgroundColor")
            anim.setFromValue_(layer.backgroundColor())
            anim.setToValue_(color.CGColor())
            anim.setDuration_(0.30)
            anim.setTimingFunction_(
                CAMediaTimingFunction.functionWithName_("easeInEaseOut")
            )
            layer.addAnimation_forKey_(anim, "bgColor")
            layer.setBackgroundColor_(color.CGColor())
        except Exception as exc:
            logger.error(f"Overlay color animation error: {exc}")
            layer.setBackgroundColor_(color.CGColor())

    # ── Voice-reactive wave bars ──────────────────────────────────────────────
    def showWaves(self):
        """Make wave bars visible (at minimum height — they react to audio)."""
        self._waves_visible = True
        for bar in self._wave_layers:
            bar.setOpacity_(1.0)
        self._current_levels = [0.0] * NUM_WAVE_BARS

    def hideWaves(self):
        self._waves_visible = False
        for bar in self._wave_layers:
            bar.removeAllAnimations()
            bar.setOpacity_(0.0)

    def updateAudioLevel_(self, level):
        """
        Called with a normalised audio level 0.0–1.0.
        Distributes the level across bars with slight per-bar variation
        for an organic look, then smoothly animates each bar's height.
        """
        if not self._waves_visible:
            return

        fh = self._pill_h

        for idx, bar in enumerate(self._wave_layers):
            # Spread: centre bar gets full level, outer bars get slightly less
            centre = (NUM_WAVE_BARS - 1) / 2.0
            dist = abs(idx - centre) / centre if centre > 0 else 0
            # Add slight per-bar phase variation using a simple hash-like offset
            variation = 0.7 + 0.3 * math.sin(idx * 2.7 + level * 6.0)
            bar_level = level * (1.0 - 0.35 * dist) * variation
            bar_level = max(0.0, min(1.0, bar_level))

            # Smooth towards target (exponential moving average)
            alpha = 0.35  # responsiveness: higher = snappier
            self._current_levels[idx] += alpha * (bar_level - self._current_levels[idx])
            cur = self._current_levels[idx]

            target_h = WAVE_BAR_MIN_H + cur * (WAVE_BAR_MAX_H - WAVE_BAR_MIN_H)
            target_y = (fh - target_h) / 2.0

            # Implicit animation via CATransaction (smooth 60fps feel)
            CATransaction.begin()
            CATransaction.setAnimationDuration_(0.08)
            CATransaction.setAnimationTimingFunction_(
                CAMediaTimingFunction.functionWithName_("easeOut")
            )
            bar_frame = bar.frame()
            bx = _rect(bar_frame)[0]
            bar.setFrame_(CGRectMake(bx, target_y, WAVE_BAR_WIDTH, target_h))
            CATransaction.commit()

    # ── Rotating arc spinner ─────────────────────────────────────────────────
    def showSpinner(self):
        """Displays a rotating arc spinner."""
        self.hideWaves()
        self._removeSpinner()

        _, _, fw, fh = _rect(self.frame())
        root = self.layer()

        arc_radius = 7.0
        line_width = 2.0
        cx = fw / 2.0
        cy = fh / 2.0

        # Draw a ~270° arc
        arc = CAShapeLayer.alloc().init()
        arc.setFrame_(((0, 0), (fw, fh)))
        path = CGPathCreateMutable()
        start_angle = 0.0
        end_angle = math.pi * 1.5  # 270°
        CGPathAddArc(path, None, cx, cy, arc_radius, start_angle, end_angle, False)
        arc.setPath_(path)
        arc.setStrokeColor_(_nscolor(1, 1, 1, 0.8).CGColor())
        arc.setFillColor_(None)
        arc.setLineWidth_(line_width)
        arc.setLineCap_("round")

        # Rotate animation
        rotation = CABasicAnimation.animationWithKeyPath_("transform.rotation.z")
        rotation.setFromValue_(0.0)
        rotation.setToValue_(2.0 * math.pi)
        rotation.setDuration_(0.9)
        rotation.setRepeatCount_(float("inf"))
        rotation.setTimingFunction_(
            CAMediaTimingFunction.functionWithName_("linear")
        )
        arc.addAnimation_forKey_(rotation, "spin")

        # Fade in
        fade = CABasicAnimation.animationWithKeyPath_("opacity")
        fade.setFromValue_(0.0)
        fade.setToValue_(1.0)
        fade.setDuration_(0.2)
        arc.addAnimation_forKey_(fade, "fadeIn")

        root.addSublayer_(arc)
        self._spinner_layer = arc

    def _removeSpinner(self):
        if self._spinner_layer:
            self._spinner_layer.removeFromSuperlayer()
            self._spinner_layer = None

    # ── Completion animation ──────────────────────────────────────────────────
    def showDone(self):
        """Displays a scale-in circle with an animated checkmark."""
        self.hideWaves()
        self._removeSpinner()
        self._removeDone()

        _, _, fw, fh = _rect(self.frame())
        root = self.layer()
        cx = fw / 2.0
        cy = fh / 2.0
        r = 10.0  # circle radius

        # ── Circle background ──
        circle = CAShapeLayer.alloc().init()
        circle.setFrame_(((0, 0), (fw, fh)))
        circle_path = CGPathCreateMutable()
        CGPathAddArc(circle_path, None, cx, cy, r, 0, 2 * math.pi, False)
        circle.setPath_(circle_path)
        circle.setFillColor_(_nscolor(1, 1, 1, 0.15).CGColor())
        circle.setStrokeColor_(None)

        # Scale-in pop
        scale = CABasicAnimation.animationWithKeyPath_("transform.scale")
        scale.setFromValue_(0.0)
        scale.setToValue_(1.0)
        scale.setDuration_(0.22)
        scale.setTimingFunction_(
            CAMediaTimingFunction.functionWithName_("easeOut")
        )
        circle.addAnimation_forKey_(scale, "pop")

        root.addSublayer_(circle)

        # ── Checkmark stroke ──
        check = CAShapeLayer.alloc().init()
        check.setFrame_(((0, 0), (fw, fh)))
        check_path = CGPathCreateMutable()
        # Proportional checkmark centred in the circle
        CGPathMoveToPoint(check_path, None, cx - 5, cy)
        CGPathAddLineToPoint(check_path, None, cx - 1.5, cy - 4.5)
        CGPathAddLineToPoint(check_path, None, cx + 6, cy + 4)
        check.setPath_(check_path)
        check.setStrokeColor_(_nscolor(1, 1, 1, 0.95).CGColor())
        check.setFillColor_(None)
        check.setLineWidth_(2.0)
        check.setLineCap_("round")
        check.setLineJoin_("round")

        # Animate stroke drawing
        draw = CABasicAnimation.animationWithKeyPath_("strokeEnd")
        draw.setFromValue_(0.0)
        draw.setToValue_(1.0)
        draw.setDuration_(0.2)
        draw.setBeginTime_(CACurrentMediaTime() + 0.1)
        draw.setFillMode_("backwards")
        draw.setTimingFunction_(
            CAMediaTimingFunction.functionWithName_("easeInEaseOut")
        )
        check.setStrokeEnd_(0.0)  # start hidden
        check.addAnimation_forKey_(draw, "drawCheck")
        # Set final value after animation
        check.setStrokeEnd_(1.0)

        root.addSublayer_(check)
        self._check_layers = [circle, check]

    def _removeDone(self):
        for layer in getattr(self, "_check_layers", []):
            layer.removeFromSuperlayer()
        self._check_layers = []


# ─── Overlay controller ──────────────────────────────────────────────────────
class Overlay:
    """
    Controller for the overlay window, managing state transitions and visibility.
    """

    def __init__(self):
        self.window = None
        self.view = None
        self._visible = False
        self._current_state = "hidden"
        self._done_timer = None
        self._setup_window()

    def _setup_window(self):
        screen = NSScreen.mainScreen()
        if screen is None:
            return
        sx, sy, sw, sh = _rect(screen.frame())

        rect = ((sx + (sw - PILL_WIDTH) / 2.0,
                 sy - PILL_HEIGHT - 20),
                (PILL_WIDTH, PILL_HEIGHT))

        self.window = OverlayPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            NSBorderlessWindowMask | NSWindowStyleMaskNonactivatingPanel,
            NSBackingStoreBuffered,
            False,
        )
        self.window.setLevel_(102)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setOpaque_(False)
        self.window.setHasShadow_(True)
        self.window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        self.window.setIgnoresMouseEvents_(True)
        self.window.setAlphaValue_(0.0)
        self.view = FlowBarView.alloc().initWithFrame_(
            ((0, 0), (PILL_WIDTH, PILL_HEIGHT))
        )
        self.window.setContentView_(self.view)
        self.window.orderFrontRegardless()

    # ── Screen helpers ────────────────────────────────────────────────────────
    def _target_screen(self):
        mouse = NSEvent.mouseLocation()
        for scr in NSScreen.screens():
            fx, fy, fw, fh = _rect(scr.frame())
            if fx <= mouse.x < fx + fw and fy <= mouse.y < fy + fh:
                return scr
        return NSScreen.mainScreen()

    def _target_position(self, screen):
        vx, vy, vw, vh = _rect(screen.visibleFrame())
        return (vx + (vw - PILL_WIDTH) / 2.0, vy + BOTTOM_MARGIN)

    def _offscreen_position(self, screen):
        sx, sy, sw, sh = _rect(screen.frame())
        return (sx + (sw - PILL_WIDTH) / 2.0, sy - PILL_HEIGHT - 20)

    # ── Slide animations ──────────────────────────────────────────────────────
    def _slide_in(self, screen):
        off = self._offscreen_position(screen)
        on = self._target_position(screen)

        self.window.setFrame_display_((off, (PILL_WIDTH, PILL_HEIGHT)), False)
        self.window.setAlphaValue_(0.0)
        self.window.orderFrontRegardless()

        # Use NSAnimationContext for reliable animation
        NSAnimationContext.beginGrouping()
        NSAnimationContext.currentContext().setDuration_(SLIDE_DURATION)
        self.window.animator().setFrame_display_(
            (on, (PILL_WIDTH, PILL_HEIGHT)), True
        )
        self.window.animator().setAlphaValue_(1.0)
        NSAnimationContext.endGrouping()
        self._visible = True

    def show_listening(self):
        self._cancel_done_timer()
        screen = self._target_screen()

        self.view._removeDone()
        self.view._removeSpinner()
        self.view.setBackgroundColor_animated_(_nscolor(*CLR_BG_DARK), False)

        if self._visible:
            self._move_to_screen(screen)
        else:
            self._slide_in(screen)

        self.view.showWaves()
        self._current_state = "listening"

    def update_audio_level(self, level):
        """Feed real-time audio amplitude (0.0–1.0) to the wave bars."""
        if self._current_state == "listening" and self.view:
            self.view.updateAudioLevel_(level)

    def show_transcribing(self):
        if self._current_state == "hidden":
            return
        self._current_state = "transcribing"

        screen = self._target_screen()
        self._move_to_screen(screen)

        self.view.hideWaves()
        self.view.setBackgroundColor_animated_(_nscolor(*CLR_PROCESSING))
        self.view.showSpinner()

    def show_done(self):
        if self._current_state == "hidden":
            return
        self._current_state = "done"

        self.view._removeSpinner()
        self.view.setBackgroundColor_animated_(_nscolor(*CLR_DONE))
        self.view.showDone()

        # Schedule auto-hide
        self._cancel_done_timer()
        
        # We use a named method for the timer target to ensure robust ref retention
        self._done_timer = threading.Timer(DONE_VISIBLE_SECS, self._timer_callback)
        self._done_timer.daemon = True
        self._done_timer.start()

    def _timer_callback(self):
        """Called by background thread timer."""
        # Pass self as sender, though ignored
        AppHelper.callAfter(self._finish_done_trampoline, None)

    def _finish_done_trampoline(self, _):
        """Called on main thread by AppHelper."""
        self._finish_done()

    def _finish_done(self):
        self.view._removeDone()
        self._slide_out()

    def hide(self):
        self._cancel_done_timer()
        self.view.hideWaves()
        self.view._removeSpinner()
        self.view._removeDone()
        self._slide_out()

    def _slide_out(self, callback=None):
        if not self._visible:
            if callback:
                callback()
            return

        screen = self._target_screen()
        off = self._offscreen_position(screen)

        # 1. Start Animation
        NSAnimationContext.beginGrouping()
        NSAnimationContext.currentContext().setDuration_(SLIDE_DURATION)
        self.window.animator().setFrame_display_(
            (off, (PILL_WIDTH, PILL_HEIGHT)), True
        )
        self.window.animator().setAlphaValue_(0.0)
        NSAnimationContext.endGrouping()

        self._visible = False
        self._current_state = "hidden"

        # 2. Force cleanup after animation to GUARANTEE it disappears
        def _cleanup():
            # Force off-screen and hide
            self.window.setFrame_display_((off, (PILL_WIDTH, PILL_HEIGHT)), False)
            self.window.orderOut_(None) 
            if callback:
                callback()
        
        # Dispatch cleanup to main thread after duration
        def _deferred():
            AppHelper.callAfter(lambda _: _cleanup(), None)
            
        t = threading.Timer(SLIDE_DURATION + 0.1, _deferred)
        t.daemon = True
        t.start()

    # Backward-compat
    def show_inactive(self):
        self.hide()

    def _cancel_done_timer(self):
        timer = getattr(self, "_done_timer", None)
        if timer is not None:
            try:
                timer.cancel()
            except Exception:
                pass
            self._done_timer = None
