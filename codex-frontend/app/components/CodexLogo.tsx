import React from "react";

interface CodexLogoProps {
  size?: number;
  className?: string;
  withGlow?: boolean;
}

export function CodexLogo({ size = 20, className = "", withGlow = true }: CodexLogoProps) {
  return (
    <div
      className={`relative inline-flex items-center justify-center shrink-0 ${className}`}
      style={{ width: size, height: size }}
    >
      {withGlow && (
        <div
          className="absolute inset-0 bg-cyan-500/20 blur-md rounded-lg pointer-events-none -z-10"
          style={{ width: size * 1.2, height: size * 1.2, margin: `-${size * 0.1}px` }}
        />
      )}
      <svg
        viewBox="0 0 32 32"
        width={size}
        height={size}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full drop-shadow-sm select-none"
      >
        <defs>
          <linearGradient id="logoBgGrad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#0F172A" />
            <stop offset="50%" stopColor="#0B1120" />
            <stop offset="100%" stopColor="#020617" />
          </linearGradient>

          <linearGradient id="logoCyanGrad" x1="8" y1="8" x2="24" y2="24" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#67E8F9" />
            <stop offset="45%" stopColor="#38BDF8" />
            <stop offset="100%" stopColor="#2563EB" />
          </linearGradient>

          <linearGradient id="logoBorderGrad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.7" />
            <stop offset="50%" stopColor="#1E293B" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#0284C7" stopOpacity="0.6" />
          </linearGradient>

          <radialGradient id="logoAmbientGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#0EA5E9" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#0EA5E9" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Outer Obsidian Frame */}
        <rect x="1" y="1" width="30" height="30" rx="8" fill="url(#logoBgGrad)" />
        <rect x="1" y="1" width="30" height="30" rx="8" stroke="url(#logoBorderGrad)" strokeWidth="1.2" />

        {/* Core Ambient Glow */}
        <circle cx="16" cy="16" r="11" fill="url(#logoAmbientGlow)" />

        {/* Layered Document Knowledge Plate */}
        <path
          d="M7.5 9.5C7.5 8.4 8.4 7.5 9.5 7.5H19L24.5 13V22.5C24.5 23.6 23.6 24.5 22.5 24.5H9.5C8.4 24.5 7.5 23.6 7.5 22.5V9.5Z"
          fill="#1E293B"
          fillOpacity="0.7"
          stroke="#38BDF8"
          strokeOpacity="0.4"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />

        {/* Document Fold Notch */}
        <path
          d="M19 7.5V12C19 12.55 19.45 13 20 13H24.5"
          stroke="#38BDF8"
          strokeOpacity="0.5"
          strokeWidth="1.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Autonomous Agent Execution Prompt: `>` */}
        <path
          d="M11.5 13L15.5 16.5L11.5 20"
          stroke="url(#logoCyanGrad)"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Execution Block Cursor: `_` */}
        <line
          x1="17.5"
          y1="20"
          x2="21"
          y2="20"
          stroke="url(#logoCyanGrad)"
          strokeWidth="2.2"
          strokeLinecap="round"
        />

        {/* Active Pulse Core */}
        <circle cx="18" cy="13" r="1.5" fill="#38BDF8" />
      </svg>
    </div>
  );
}
