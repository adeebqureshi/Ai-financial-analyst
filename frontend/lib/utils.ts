import { clsx, type ClassValue } from "clsx"
import { extendTailwindMerge } from "tailwind-merge"

/**
 * The design system declares a custom type scale in `@theme` (`--text-display`,
 * `--text-title`, `--text-subtitle`, `--text-metric`, `--text-body`,
 * `--text-label`, `--text-caption`), which Tailwind exposes as `text-*`
 * utilities.
 *
 * tailwind-merge has no way of knowing those are font sizes, so it assumes an
 * unknown `text-*` value is a *colour* and puts it in the same conflict group
 * as `text-primary-foreground`. Because our button size variants append
 * `text-label` after the variant's colour, the earlier colour class was being
 * silently dropped — e.g. the primary button rendered `bg-primary` with the
 * inherited dark text instead of `text-primary-foreground` (≈1.7:1 contrast).
 *
 * Teaching tailwind-merge about the type scale keeps colours and sizes in
 * separate groups, so both survive the merge.
 */
const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [
        {
          text: [
            "display",
            "title",
            "subtitle",
            "metric",
            "body",
            "label",
            "caption",
          ],
        },
      ],
    },
  },
})

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
