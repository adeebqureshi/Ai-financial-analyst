import { redirect } from "next/navigation";

/**
 * `/dashboard` is a retired Command Hub route. It now redirects to the
 * application's primary destination, `/analysis`, so old links and bookmarks
 * keep working instead of 404ing.
 */
export default function DashboardPage() {
  redirect("/analysis");
}
