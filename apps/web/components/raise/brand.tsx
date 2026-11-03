import { LeafIcon } from "lucide-react";

import { cn } from "@/lib/utils";

/** The RAISE mark: a leaf on a deep-canopy tile. */
export function BrandMark({ size = "md", className }: { size?: "sm" | "md" | "lg"; className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "bg-brand text-brand-foreground inline-flex shrink-0 items-center justify-center shadow-[inset_0_-1px_0_rgb(0_0_0/0.25)]",
        size === "sm" && "size-7 rounded-lg [&_svg]:size-4",
        size === "md" && "size-9 rounded-xl [&_svg]:size-5",
        size === "lg" && "size-14 rounded-2xl [&_svg]:size-7",
        className
      )}
    >
      <LeafIcon strokeWidth={2.25} />
    </span>
  );
}

export function BrandLockup({ tagline }: { tagline?: string }) {
  return (
    <span className="flex min-w-0 items-center gap-2.5">
      <BrandMark size="sm" />
      <span className="flex min-w-0 flex-col leading-tight">
        <span className="text-foreground text-[0.95rem] font-semibold tracking-wide">RAISE</span>
        {tagline && <span className="text-muted-foreground truncate text-[0.7rem]">{tagline}</span>}
      </span>
    </span>
  );
}
