import { redirect } from "next/navigation";

/**
 * The standalone Company workflow was consolidated into Analyze, which already
 * carries the full company research experience (profile, market, valuation,
 * health, risk, AI insights and the research report). This route is kept only
 * so old links and bookmarks land somewhere real instead of 404ing.
 */
export default function CompanyPage() {
  redirect("/analysis");
}