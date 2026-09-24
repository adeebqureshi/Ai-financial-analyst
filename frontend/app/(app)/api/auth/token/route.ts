import { NextResponse } from "next/server";

export async function POST() {
  const username = process.env.DEV_AUTH_USERNAME;
  const password = process.env.DEV_AUTH_PASSWORD;
  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";

  if (!username || !password) {
    return NextResponse.json(
      { detail: "Development auth credentials are not configured." },
      { status: 500 }
    );
  }

  const body = new URLSearchParams({
    username,
    password,
  });

  const response = await fetch(`${apiUrl}/auth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
    cache: "no-store",
  });

  const text = await response.text();

  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}