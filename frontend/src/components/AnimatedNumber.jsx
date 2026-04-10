import { useEffect, useRef, useState } from 'react'

export default function AnimatedNumber({ value, duration = 600, formatter }) {
  const safeValue = Number(value)
  const target = Number.isFinite(safeValue) ? safeValue : 0
  const [displayValue, setDisplayValue] = useState(target)
  const previousRef = useRef(target)
  const frameRef = useRef(null)

  useEffect(() => {
    const startValue = previousRef.current
    const delta = target - startValue

    if (Math.abs(delta) < 0.0001) {
      setDisplayValue(target)
      return () => {}
    }

    const startTime = performance.now()

    const easeOutCubic = (t) => 1 - (1 - t) ** 3

    const tick = (now) => {
      const elapsed = now - startTime
      const progress = Math.min(1, elapsed / duration)
      const nextValue = startValue + delta * easeOutCubic(progress)
      setDisplayValue(nextValue)

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick)
      } else {
        previousRef.current = target
      }
    }

    frameRef.current = requestAnimationFrame(tick)

    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current)
      }
    }
  }, [target, duration])

  return <>{formatter ? formatter(displayValue) : displayValue}</>
}
