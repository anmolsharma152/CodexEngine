import React from "react";

interface CodexLogoProps {
  size?: number;
  className?: string;
  withGlow?: boolean;
}

export function CodexLogo({ size = 22, className = "", withGlow = true }: CodexLogoProps) {
  return (
    <div
      className={`relative inline-flex items-center justify-center shrink-0 ${className}`}
      style={{ width: size, height: size }}
    >
      {withGlow && (
        <div
          className="absolute inset-0 bg-sky-500/20 blur-md rounded-lg pointer-events-none -z-10"
          style={{ width: size * 1.25, height: size * 1.25, margin: `-${size * 0.125}px` }}
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
          <linearGradient id="reactLogoBg" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#0F172A" />
            <stop offset="100%" stopColor="#020617" />
          </linearGradient>

          <linearGradient id="reactTopPlate" x1="7.5" y1="6" x2="24.5" y2="15" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#38BDF8" />
            <stop offset="100%" stopColor="#0EA5E9" />
          </linearGradient>

          <linearGradient id="reactMidPlate" x1="7.5" y1="12" x2="24.5" y2="21" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#60A5FA" />
            <stop offset="100%" stopColor="#3B82F6" />
          </linearGradient>

          <linearGradient id="reactBotPlate" x1="7.5" y1="18" x2="24.5" y2="27" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#818CF8" />
            <stop offset="100%" stopColor="#6366F1" />
          </linearGradient>

          <linearGradient id="reactBorderGrad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#6366F1" stopOpacity="0.3" />
          </linearGradient>
        </defs>

        {/* Squircle Base Frame */}
        <rect x="1" y="1" width="30" height="30" rx="8" fill="url(#reactLogoBg)" stroke="url(#reactBorderGrad)" strokeWidth="1.2" />

        {/* Layer 3: Storage & Artifact Foundation */}
        <path
          d="M16 18L24.5 22.5L16 27L7.5 22.5L16 18Z"
          fill="url(#reactBotPlate)"
          fillOpacity="0.4"
          stroke="url(#reactBotPlate)"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />

        {/* Layer 2: Hybrid Retrieval & Memory Pipeline */}
        <path
          d="M16 12L24.5 16.5L16 21L7.5 16.5L16 12Z"
          fill="url(#reactMidPlate)"
          fillOpacity="0.6"
          stroke="url(#reactMidPlate)"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />

        {/* Layer 1: Autonomous Cognitive Agent Engine */}
        <path
          d="M16 6L24.5 10.5L16 15L7.5 10.5L16 6Z"
          fill="url(#reactTopPlate)"
          stroke="#BAE6FD"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />

        {/* Center Nexus Core */}
        <circle cx="16" cy="10.5" r="1.5" fill="#FFFFFF" />
      </svg>
    </div>
  );
}
