// One motion loop: Lenis smooth scroll driven by GSAP's ticker, ScrollTrigger kept in sync.
import { useEffect, useRef, type ReactNode } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import Lenis from 'lenis'

gsap.registerPlugin(ScrollTrigger, useGSAP)

let lenis: Lenis | null = null

export const prefersReducedMotion = () =>
  typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

export function useSmoothScroll() {
  useEffect(() => {
    lenis = new Lenis({ lerp: 0.1, anchors: true, allowNestedScroll: true, stopInertiaOnNavigate: true })
    lenis.on('scroll', ScrollTrigger.update)
    const tick = (time: number) => lenis?.raf(time * 1000)
    gsap.ticker.add(tick)
    gsap.ticker.lagSmoothing(0)
    return () => {
      gsap.ticker.remove(tick)
      lenis?.destroy()
      lenis = null
    }
  }, [])
}

export function scrollToTop() {
  if (lenis) lenis.scrollTo(0, { immediate: true, force: true })
  else window.scrollTo(0, 0)
  requestAnimationFrame(() => ScrollTrigger.refresh())
}

export function lockScroll(locked: boolean) {
  if (!lenis) return
  if (locked) lenis.stop()
  else lenis.start()
}

/**
 * Headline reveal. Content is visible by default; it is only held back when it starts
 * below the fold, and an IntersectionObserver (no precomputed scroll positions) lets it in.
 */
export function Reveal({ children, className = '', delay = 0, as: Tag = 'div' }: { children: ReactNode; className?: string; delay?: number; as?: 'div' | 'section' | 'header' }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = ref.current
    if (!el || prefersReducedMotion() || typeof IntersectionObserver === 'undefined') return
    if (el.getBoundingClientRect().top < window.innerHeight * 0.9) return
    el.classList.add('reveal-pending')
    el.style.transitionDelay = `${delay}s`
    const io = new IntersectionObserver(
      entries => {
        if (entries.some(e => e.isIntersecting)) {
          el.classList.remove('reveal-pending')
          io.disconnect()
        }
      },
      { rootMargin: '0px 0px -8% 0px' },
    )
    io.observe(el)
    return () => {
      io.disconnect()
      el.classList.remove('reveal-pending')
    }
  }, [delay])
  return (
    <Tag ref={ref as never} className={`reveal ${className}`}>
      {children}
    </Tag>
  )
}

/**
 * Card entrance for a freshly rendered page: cards already on screen rise in with a short
 * stagger; cards below the fold are released by an IntersectionObserver as they scroll in.
 */
export function useCardEntrance(key: unknown) {
  useEffect(() => {
    if (prefersReducedMotion()) return
    const cards = Array.from(document.querySelectorAll<HTMLElement>('.content .reveal-card'))
    const vh = window.innerHeight
    const visible = cards.filter(c => c.getBoundingClientRect().top < vh)
    const later = cards.filter(c => !visible.includes(c))
    const tween = gsap.from(visible, { y: 14, autoAlpha: 0, duration: 0.7, ease: 'expo.out', stagger: 0.035, clearProps: 'transform,opacity,visibility' })
    later.forEach(c => c.classList.add('reveal', 'reveal-pending'))
    const io = new IntersectionObserver(
      entries =>
        entries.forEach(e => {
          if (e.isIntersecting) {
            e.target.classList.remove('reveal-pending')
            io.unobserve(e.target)
          }
        }),
      { rootMargin: '0px 0px -6% 0px' },
    )
    later.forEach(c => io.observe(c))
    return () => {
      tween.revert()
      io.disconnect()
      later.forEach(c => c.classList.remove('reveal-pending'))
    }
  }, [key])
}

/** Recompute ScrollTrigger positions once fonts and late layout have settled. */
export function useScrollRefresh() {
  useEffect(() => {
    const refresh = () => ScrollTrigger.refresh()
    document.fonts?.ready.then(refresh).catch(() => undefined)
    window.addEventListener('load', refresh)
    const t = window.setTimeout(refresh, 1200)
    return () => {
      window.removeEventListener('load', refresh)
      window.clearTimeout(t)
    }
  }, [])
}
