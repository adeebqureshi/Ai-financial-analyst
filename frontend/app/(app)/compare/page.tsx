import { ComparisonHero } from "@/components/comparison/comparison-hero";
import { ComparisonWorkspace } from "@/components/comparison/comparison-workspace";

export default function ComparePage() {
  return (
    <div className="mx-auto max-w-[100rem] space-y-6 pb-8">
      <ComparisonHero />

      <ComparisonWorkspace />
    </div>
  );
}
