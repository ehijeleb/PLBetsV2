import clsx from "clsx";
import { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
  padded?: boolean;
}

export function Card({ elevated, padded = true, className, children, ...rest }: CardProps) {
  return (
    <div
      className={clsx(
        "bg-bg-secondary border border-line rounded-2xl",
        padded && "p-5",
        elevated && "shadow-[0_8px_30px_-12px_rgba(0,0,0,0.6)]",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx("flex items-center justify-between mb-4", className)} {...rest}>
      {children}
    </div>
  );
}

export function CardTitle({ className, children, ...rest }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={clsx(
        "font-display tracking-wide text-xl uppercase text-ink",
        className,
      )}
      {...rest}
    >
      {children}
    </h3>
  );
}
