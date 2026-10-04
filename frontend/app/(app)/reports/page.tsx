import { redirect } from "next/navigation";

/**
 * The standalone Reports workflow was consolidated into Analyze. Report
 * generation is now the final step of `/analysis/[ticker]`.
 *
 * The old page collected its ticker from a form field, never from the URL, so
 * there is no query parameter to carry over and none is invented here.
 */
export default function ReportsPage() {
  redirect("/analysis");
}