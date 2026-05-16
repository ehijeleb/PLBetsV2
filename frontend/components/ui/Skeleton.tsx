import clsx from "clsx";

interface SkeletonProps {
  className?: string;
  width?: string;
  height?: string;
}

export function Skeleton({ className, width, height }: SkeletonProps) {
  return (
    <div
      className={clsx("skeleton rounded-md", className)}
      style={{ width, height }}
      aria-hidden
    />
  );
}
