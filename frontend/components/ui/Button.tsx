"use client";
import clsx from "clsx";
import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost";
type Size = "sm" | "md" | "lg" | "xl";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  fullWidth?: boolean;
  loading?: boolean;
}

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-accent-green text-bg-primary hover:brightness-110 active:brightness-95 disabled:opacity-40 shadow-glow font-semibold tracking-wide",
  secondary:
    "bg-bg-tertiary text-ink border border-line hover:border-accent-green/40 disabled:opacity-40",
  ghost:
    "bg-transparent text-ink hover:bg-bg-tertiary disabled:opacity-40",
};

const SIZES: Record<Size, string> = {
  sm: "text-xs px-3 py-1.5 rounded-md",
  md: "text-sm px-4 py-2 rounded-lg",
  lg: "text-base px-6 py-3 rounded-lg",
  xl: "text-lg px-8 py-4 rounded-xl uppercase tracking-widest",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", fullWidth, loading, className, children, disabled, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={clsx(
        "inline-flex items-center justify-center gap-2 transition-all select-none",
        VARIANTS[variant],
        SIZES[size],
        fullWidth && "w-full",
        loading && "cursor-wait",
        className,
      )}
      {...rest}
    >
      {loading ? <Spinner /> : null}
      {children}
    </button>
  );
});

function Spinner() {
  return (
    <span
      aria-hidden
      className="inline-block w-4 h-4 border-2 border-current border-r-transparent rounded-full animate-spin"
    />
  );
}
