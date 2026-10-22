// Motion is deliberately small: native scrolling, a short fade when a page settles (CSS),
// and the drawer sliding in. Nothing reads the pointer and nothing loops.

export const prefersReducedMotion = () =>
  typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

export function scrollToTop() {
  window.scrollTo(0, 0)
}

/** Stop the page scrolling behind the drawer. */
export function lockScroll(locked: boolean) {
  document.documentElement.style.overflow = locked ? 'hidden' : ''
}
