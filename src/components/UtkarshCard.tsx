import React, { useEffect, useRef, useCallback, useMemo } from "react";
import "./UtkarshCard.css";

interface UtkarshCardProps {
  onContactClick?: () => void;
}

const DEFAULT_BEHIND_GRADIENT =
  "radial-gradient(farthest-side circle at var(--pointer-x) var(--pointer-y),hsla(266,100%,90%,calc(var(--card-opacity)*0.3)) 4%,hsla(266,50%,80%,calc(var(--card-opacity)*0.2)) 10%,hsla(266,25%,70%,calc(var(--card-opacity)*0.1)) 50%,hsla(266,0%,60%,0) 100%),radial-gradient(35% 52% at 55% 20%,#00ffaa44 0%,#073aff00 100%),radial-gradient(100% 100% at 50% 50%,#00c1ff44 1%,#073aff00 76%),conic-gradient(from 124deg at 50% 50%,#c137ff44 0%,#07c6ff44 40%,#07c6ff44 60%,#c137ff44 100%)";

const DEFAULT_INNER_GRADIENT =
  "linear-gradient(145deg,#60496e8c 0%,#71C4FF44 100%)";

const ANIMATION_CONFIG = {
  SMOOTH_DURATION: 600,
  INITIAL_DURATION: 1500,
  INITIAL_X_OFFSET: 70,
  INITIAL_Y_OFFSET: 60,
} as const;

const clamp = (value: number, min = 0, max = 100): number =>
  Math.min(Math.max(value, min), max);

const round = (value: number, precision = 3): number =>
  parseFloat(value.toFixed(precision));

const adjust = (
  value: number,
  fromMin: number,
  fromMax: number,
  toMin: number,
  toMax: number
): number =>
  round(toMin + ((toMax - toMin) * (value - fromMin)) / (fromMax - fromMin));

const easeInOutCubic = (x: number): number =>
  x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;

const UtkarshCard: React.FC<UtkarshCardProps> = ({ onContactClick }) => {
  const wrapRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  const animationHandlers = useMemo(() => {
    let rafId: number | null = null;

    const updateCardTransform = (
      offsetX: number,
      offsetY: number,
      card: HTMLElement,
      wrap: HTMLElement
    ) => {
      const width = card.clientWidth;
      const height = card.clientHeight;

      const percentX = clamp((100 / width) * offsetX);
      const percentY = clamp((100 / height) * offsetY);

      const centerX = percentX - 50;
      const centerY = percentY - 50;

      const properties = {
        "--pointer-x": `${percentX}%`,
        "--pointer-y": `${percentY}%`,
        "--background-x": `${adjust(percentX, 0, 100, 35, 65)}%`,
        "--background-y": `${adjust(percentY, 0, 100, 35, 65)}%`,
        "--pointer-from-center": `${clamp(Math.hypot(percentY - 50, percentX - 50) / 50, 0, 1)}`,
        "--pointer-from-top": `${percentY / 100}`,
        "--pointer-from-left": `${percentX / 100}`,
        "--rotate-x": `${round(-(centerX / 5))}deg`,
        "--rotate-y": `${round(centerY / 4)}deg`,
      };

      Object.entries(properties).forEach(([property, value]) => {
        wrap.style.setProperty(property, value);
      });
    };

    const createSmoothAnimation = (
      duration: number,
      startX: number,
      startY: number,
      card: HTMLElement,
      wrap: HTMLElement
    ) => {
      const startTime = performance.now();
      const targetX = wrap.clientWidth / 2;
      const targetY = wrap.clientHeight / 2;

      const animationLoop = (currentTime: number) => {
        const elapsed = currentTime - startTime;
        const progress = clamp(elapsed / duration);
        const easedProgress = easeInOutCubic(progress);

        const currentX = adjust(easedProgress, 0, 1, startX, targetX);
        const currentY = adjust(easedProgress, 0, 1, startY, targetY);

        updateCardTransform(currentX, currentY, card, wrap);

        if (progress < 1) {
          rafId = requestAnimationFrame(animationLoop);
        }
      };

      rafId = requestAnimationFrame(animationLoop);
    };

    return {
      updateCardTransform,
      createSmoothAnimation,
      cancelAnimation: () => {
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
      },
    };
  }, []);

  const handlePointerMove = useCallback(
    (event: PointerEvent) => {
      const card = cardRef.current;
      const wrap = wrapRef.current;

      if (!card || !wrap || !animationHandlers) return;

      const rect = card.getBoundingClientRect();
      animationHandlers.updateCardTransform(
        event.clientX - rect.left,
        event.clientY - rect.top,
        card,
        wrap
      );
    },
    [animationHandlers]
  );

  const handlePointerEnter = useCallback(() => {
    const card = cardRef.current;
    const wrap = wrapRef.current;

    if (!card || !wrap || !animationHandlers) return;

    animationHandlers.cancelAnimation();
    wrap.classList.add("active");
    card.classList.add("active");
  }, [animationHandlers]);

  const handlePointerLeave = useCallback(
    (event: PointerEvent) => {
      const card = cardRef.current;
      const wrap = wrapRef.current;

      if (!card || !wrap || !animationHandlers) return;

      animationHandlers.createSmoothAnimation(
        ANIMATION_CONFIG.SMOOTH_DURATION,
        event.offsetX,
        event.offsetY,
        card,
        wrap
      );
      wrap.classList.remove("active");
      card.classList.remove("active");
    },
    [animationHandlers]
  );

  useEffect(() => {
    if (!animationHandlers) return;

    const card = cardRef.current;
    const wrap = wrapRef.current;

    if (!card || !wrap) return;

    const pointerMoveHandler = handlePointerMove as EventListener;
    const pointerEnterHandler = handlePointerEnter as EventListener;
    const pointerLeaveHandler = handlePointerLeave as EventListener;

    card.addEventListener("pointerenter", pointerEnterHandler);
    card.addEventListener("pointermove", pointerMoveHandler);
    card.addEventListener("pointerleave", pointerLeaveHandler);

    const initialX = wrap.clientWidth - ANIMATION_CONFIG.INITIAL_X_OFFSET;
    const initialY = ANIMATION_CONFIG.INITIAL_Y_OFFSET;

    animationHandlers.updateCardTransform(initialX, initialY, card, wrap);
    animationHandlers.createSmoothAnimation(
      ANIMATION_CONFIG.INITIAL_DURATION,
      initialX,
      initialY,
      card,
      wrap
    );

    return () => {
      card.removeEventListener("pointerenter", pointerEnterHandler);
      card.removeEventListener("pointermove", pointerMoveHandler);
      card.removeEventListener("pointerleave", pointerLeaveHandler);
      animationHandlers.cancelAnimation();
    };
  }, [animationHandlers, handlePointerMove, handlePointerEnter, handlePointerLeave]);

  const cardStyle = useMemo(
    () =>
      ({
        "--icon": "none",
        "--grain": "none",
        "--behind-gradient": DEFAULT_BEHIND_GRADIENT,
        "--inner-gradient": DEFAULT_INNER_GRADIENT,
      }) as React.CSSProperties,
    []
  );

  const handleContactClick = useCallback(() => {
    onContactClick?.();
  }, [onContactClick]);

  return (
    <div
      ref={wrapRef}
      className="utkarsh-card-wrapper"
      style={cardStyle}
    >
      <section ref={cardRef} className="utkarsh-card">
        <div className="utkarsh-inside">
          <div className="utkarsh-shine" />
          <div className="utkarsh-glare" />
          <div className="utkarsh-content utkarsh-avatar-content">
            <img
              className="utkarsh-avatar"
              src="/images/utkarsh.png"
              alt="Utkarsh avatar"
              loading="lazy"
              onError={(e) => {
                console.error(`Failed to load Utkarsh avatar`);
                const target = e.target as HTMLImageElement;
                target.style.opacity = "0.5";
                target.style.backgroundColor = "rgba(255, 255, 255, 0.1)";
              }}
              onLoad={() => {
                console.log(`Successfully loaded Utkarsh avatar`);
              }}
            />
            <div className="utkarsh-user-info">
              <div className="utkarsh-user-details">
                <div className="utkarsh-mini-avatar">
                  <img
                    src="/images/utkarsh.png"
                    alt="Utkarsh mini avatar"
                    loading="lazy"
                  />
                </div>
                <div className="utkarsh-user-text">
                  <div className="utkarsh-handle">@utkarsh_raj.028</div>
                  <div className="utkarsh-status">AI, Finance and Physics</div>
                </div>
              </div>
              <a
                href="https://sutihar.com/utkarsh"
                target="_blank"
                rel="noopener noreferrer"
                className="utkarsh-contact-btn"
                style={{ pointerEvents: "auto", textDecoration: "none", display: "flex", alignItems: "center", justifyContent: "center" }}
                aria-label="Contact Utkarsh"
              >
                Connect
              </a>
            </div>
          </div>
          <div className="utkarsh-content">
            <div className="utkarsh-details">
              <h3>Utkarsh</h3>
              <p>AI & Data Scientist</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default UtkarshCard; 