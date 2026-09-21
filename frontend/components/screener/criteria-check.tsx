"use client";

import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Loader2, Search, XCircle } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ErrorInline } from "@/components/ui/error-display";
import { Field, Input, TickerInput } from "@/components/ui/field";
import { api } from "@/services/api";
import type {
  AnalyzeData,
  ApiResponse,
  ScreenData,
  ScreenItemData,
  ScreenRequestData,
} from "@/types/analysis";

type Criteria = {
  min_piotroski: string;
  min_altman: string;
  max_beneish: string;
  min_upside: string;
  max_results: string;
};

/**
 * Screening thresholds. Prefilled with the backend's own `ScreenRequest`
 * defaults so the user starts from a documented baseline, never an invented
 * application value.
 */
const defaultCriteria: Criteria = {
  min_piotroski: "0",
  min_altman: "0",
  max_beneish: "100",
  min_upside: "-100",
  max_results: "10",
};

type Assumptions = {
  growth_rate: string;
  risk_free_rate: string;
  beta: string;
  market_return: string;
  tax_rate: string;
  cost_of_debt: string;
  terminal_growth: string;
  years: string;
};

/**
 * Valuation assumptions left blank until the user provides them, except the
 * three fields the backend `ValuationParams` schema documents as having
 * defaults (cost_of_debt 0.05, terminal_growth 0.03, years 5). Beta and the
 * other rates are never invented — they are either prefilled from real
 * `/analyze` market data or required from the user.
 */
const baseAssumptions: Assumptions = {
  growth_rate: "",
  risk_free_rate: "",
  beta: "",
  market_return: "",
  tax_rate: "",
  cost_of_debt: "0.05",
  terminal_growth: "0.03",
  years: "5",
};

function toNumber(value: string): number | null {
  if (value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Schema ranges mirrored from the backend `ValuationParams`/`ScreenRequest`. */
function validate(
  criteria: Criteria,
  assumptions: Assumptions,
  betaAvailable: boolean,
  currentPriceAvailable: boolean,
  currentPrice: string
): Record<string, string> {
  const errors: Record<string, string> = {};

  const minPiotroski = toNumber(criteria.min_piotroski);
  if (
    minPiotroski === null ||
    !Number.isInteger(minPiotroski) ||
    minPiotroski < 0 ||
    minPiotroski > 9
  ) {
    errors.min_piotroski = "Enter an integer between 0 and 9.";
  }

  const minAltman = toNumber(criteria.min_altman);
  if (minAltman === null || minAltman < 0) {
    errors.min_altman = "Enter a number of 0 or more.";
  }

  const maxBeneish = toNumber(criteria.max_beneish);
  if (maxBeneish === null) {
    errors.max_beneish = "Enter a maximum Beneish M-Score.";
  }

  const minUpside = toNumber(criteria.min_upside);
  if (minUpside === null) {
    errors.min_upside = "Enter a minimum upside percentage.";
  }

  const maxResults = toNumber(criteria.max_results);
  if (
    maxResults === null ||
    !Number.isInteger(maxResults) ||
    maxResults < 1 ||
    maxResults > 100
  ) {
    errors.max_results = "Enter an integer between 1 and 100.";
  }

  const growth = toNumber(assumptions.growth_rate);
  if (growth === null || growth < 0 || growth > 1) {
    errors.growth_rate = "Enter a growth rate between 0 and 1 (e.g. 0.08 = 8%).";
  }

  const riskFree = toNumber(assumptions.risk_free_rate);
  if (riskFree === null || riskFree < 0 || riskFree > 1) {
    errors.risk_free_rate = "Enter a rate between 0 and 1 (e.g. 0.0425 = 4.25%).";
  }

  const marketReturn = toNumber(assumptions.market_return);
  if (marketReturn === null || marketReturn < 0 || marketReturn > 1) {
    errors.market_return = "Enter a rate between 0 and 1 (e.g. 0.10 = 10%).";
  }

  const tax = toNumber(assumptions.tax_rate);
  if (tax === null || tax < 0 || tax > 1) {
    errors.tax_rate = "Enter a tax rate between 0 and 1 (e.g. 0.21 = 21%).";
  }

  const costOfDebt = toNumber(assumptions.cost_of_debt);
  if (costOfDebt === null || costOfDebt < 0 || costOfDebt > 1) {
    errors.cost_of_debt = "Enter a rate between 0 and 1.";
  }

  const terminalGrowth = toNumber(assumptions.terminal_growth);
  if (terminalGrowth === null || terminalGrowth < 0 || terminalGrowth > 1) {
    errors.terminal_growth = "Enter a rate between 0 and 1 (e.g. 0.03 = 3%).";
  }

  const years = toNumber(assumptions.years);
  if (
    years === null ||
    !Number.isInteger(years) ||
    years < 1 ||
    years > 30
  ) {
    errors.years = "Enter an integer between 1 and 30.";
  }

  // Beta: prefilled from real market data when available; otherwise the
  // user must supply it. No fabricated fallback.
  if (!betaAvailable) {
    const beta = toNumber(assumptions.beta);
    if (beta === null || beta < 0) {
      errors.beta =
        "Beta is not available from market data — enter a value to use.";
    }
  }

  // Current price comes from real market data when available; otherwise the
  // user must supply it for the valuation to be computed.
  if (!currentPriceAvailable) {
    const price = toNumber(currentPrice);
    if (price === null || price < 0) {
      errors.current_price =
        "Current price is unavailable from market data — enter the price to use.";
    }
  }

  return errors;
}

function DataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border py-2 last:border-0">
      <dt className="text-caption text-subtle-foreground">{label}</dt>
      <dd className="text-body font-medium text-foreground">{value}</dd>
    </div>
  );
}

export function CriteriaCheck() {
  const [ticker, setTicker] = useState("");
  const [tickerError, setTickerError] = useState<string | null>(null);
  const [criteria, setCriteria] = useState<Criteria>(defaultCriteria);
  const [assumptions, setAssumptions] = useState<Assumptions>(baseAssumptions);
  const [manualPrice, setManualPrice] = useState("");
  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({});

  const analysisMutation = useMutation({
    mutationFn: (symbol: string) => api.analyze(symbol),
  });

  const screenMutation = useMutation({
    mutationFn: (body: ScreenRequestData) => api.screen(body),
  });

  const analysis: AnalyzeData | null =
    (analysisMutation.data as ApiResponse<AnalyzeData> | undefined)?.data ??
    null;

  const screenResult: ScreenData | null =
    (screenMutation.data as ApiResponse<ScreenData> | undefined)?.data ?? null;

  const marketPrice = analysis?.market?.current_price ?? null;
  const currentPriceAvailable = marketPrice !== null;
  const betaAvailable = analysis?.market?.beta != null;

  const effectiveBeta = betaAvailable
    ? String(analysis!.market.beta)
    : assumptions.beta;

  function fetchAnalysis() {
    const symbol = ticker.trim().toUpperCase();

    if (!symbol) {
      setTickerError("Enter a ticker symbol.");
      return;
    }

    setTickerError(null);
    setValidationErrors({});
    screenMutation.reset();
    analysisMutation.mutate(symbol);
  }

  function runCheck() {
    if (!analysis || !analysis.statement) return;

    const errors = validate(
      criteria,
      assumptions,
      betaAvailable,
      currentPriceAvailable,
      manualPrice
    );
    setValidationErrors(errors);

    if (Object.keys(errors).length > 0) return;

    const currentPrice = currentPriceAvailable
      ? (marketPrice as number)
      : (toNumber(manualPrice) as number);

    screenMutation.mutate({
      min_piotroski: toNumber(criteria.min_piotroski)!,
      min_altman: toNumber(criteria.min_altman)!,
      max_beneish: toNumber(criteria.max_beneish)!,
      min_upside: toNumber(criteria.min_upside)!,
      max_results: toNumber(criteria.max_results)!,
      statement: analysis.statement,
      valuation: {
        current_price: currentPrice,
        growth_rate: toNumber(assumptions.growth_rate)!,
        risk_free_rate: toNumber(assumptions.risk_free_rate)!,
        beta: Number(effectiveBeta),
        market_return: toNumber(assumptions.market_return)!,
        tax_rate: toNumber(assumptions.tax_rate)!,
        cost_of_debt: toNumber(assumptions.cost_of_debt)!,
        terminal_growth: toNumber(assumptions.terminal_growth)!,
        years: toNumber(assumptions.years)!,
      },
    });
  }

  const setAssumption = (key: keyof Assumptions, value: string) =>
    setAssumptions((prev) => ({ ...prev, [key]: value }));

  const setCriterion = (key: keyof Criteria, value: string) =>
    setCriteria((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="space-y-8">
      {/* Step 1 — candidate ticker */}
      <section
        aria-labelledby="criteria-ticker-heading"
        className="rounded-xl border border-border bg-card p-6"
      >
        <h2
          id="criteria-ticker-heading"
          className="text-title font-semibold text-foreground"
        >
          1. Candidate company
        </h2>

        <p className="mt-1 text-caption text-subtle-foreground">
          The criteria check evaluates one company. Its real analysis data is
          fetched from <code>/analyze</code> first.
        </p>

        <div className="mt-4 flex flex-wrap items-end gap-3">
          <Field
            label="Ticker"
            htmlFor="criteria-ticker"
            error={tickerError ?? undefined}
            required
            className="w-40"
          >
            <TickerInput
              id="criteria-ticker"
              value={ticker}
              onValueChange={(value) => {
                setTicker(value);
                setTickerError(null);
              }}
              aria-invalid={tickerError ? true : undefined}
              placeholder="AAPL"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  fetchAnalysis();
                }
              }}
            />
          </Field>

          <Button
            onClick={fetchAnalysis}
            disabled={analysisMutation.isPending}
          >
            {analysisMutation.isPending ? (
              <Loader2
                size={16}
                className="motion-safe:animate-spin"
                aria-hidden="true"
              />
            ) : (
              <Search size={16} aria-hidden="true" />
            )}
            {analysisMutation.isPending ? "Fetching…" : "Fetch analysis"}
          </Button>
        </div>

        {analysisMutation.isError && (
          <div className="mt-4">
            <ErrorInline
              error={analysisMutation.error}
              onRetry={() => analysisMutation.mutate(ticker.trim().toUpperCase())}
            />
          </div>
        )}

        {analysis && (
          <dl className="mt-6 grid gap-x-8 sm:grid-cols-2" data-testid="criteria-company-data">
            <div>
              <p className="mb-2 text-caption font-medium uppercase tracking-wide text-subtle-foreground">
                Company data (from /analyze)
              </p>
              <DataRow label="Company" value={analysis.company.name} />
              <DataRow label="Ticker" value={analysis.company.ticker} />
              <DataRow
                label="Current price"
                value={
                  currentPriceAvailable
                    ? `$${marketPrice!.toFixed(2)}`
                    : "Unavailable"
                }
              />
              <DataRow
                label="Beta"
                value={betaAvailable ? analysis!.market.beta!.toFixed(2) : "Unavailable"}
              />
            </div>
            <div>
              <p className="mb-2 mt-6 text-caption font-medium uppercase tracking-wide text-subtle-foreground sm:mt-0">
                Health scores (from /analyze)
              </p>
              <DataRow
                label="Piotroski F-Score"
                value={`${analysis.health.piotroski_score}/9`}
              />
              <DataRow label="Altman Z-Score" value={analysis.health.altman_score.toFixed(2)} />
              <DataRow label="Beneish M-Score" value={analysis.health.beneish_score.toFixed(2)} />
              <DataRow
                label="Health"
                value={`${analysis.health.score}/100 · ${analysis.health.rating}`}
              />
            </div>
          </dl>
        )}
      </section>

      {/* Steps 2 + 3 — criteria and assumptions */}
      {analysis && (
        <>
          <section
            aria-labelledby="criteria-heading"
            className="rounded-xl border border-border bg-card p-6"
          >
            <h2
              id="criteria-heading"
              className="text-title font-semibold text-foreground"
            >
              2. Screening criteria
            </h2>

            <p className="mt-1 text-caption text-subtle-foreground">
              Thresholds the candidate must meet. Prefilled with the backend
              endpoint&apos;s documented defaults.
            </p>

            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Field
                label="Min Piotroski F-Score"
                htmlFor="criteria-min-piotroski"
                error={validationErrors.min_piotroski}
                required
              >
                <Input
                  id="criteria-min-piotroski"
                  type="number"
                  min={0}
                  max={9}
                  step={1}
                  value={criteria.min_piotroski}
                  onChange={(event) => setCriterion("min_piotroski", event.target.value)}
                  aria-invalid={validationErrors.min_piotroski ? true : undefined}
                />
              </Field>

              <Field
                label="Min Altman Z-Score"
                htmlFor="criteria-min-altman"
                error={validationErrors.min_altman}
                required
              >
                <Input
                  id="criteria-min-altman"
                  type="number"
                  min={0}
                  step={0.1}
                  value={criteria.min_altman}
                  onChange={(event) => setCriterion("min_altman", event.target.value)}
                  aria-invalid={validationErrors.min_altman ? true : undefined}
                />
              </Field>

              <Field
                label="Max Beneish M-Score"
                htmlFor="criteria-max-beneish"
                hint="Lower is better."
                error={validationErrors.max_beneish}
                required
              >
                <Input
                  id="criteria-max-beneish"
                  type="number"
                  step={0.1}
                  value={criteria.max_beneish}
                  onChange={(event) => setCriterion("max_beneish", event.target.value)}
                  aria-invalid={validationErrors.max_beneish ? true : undefined}
                />
              </Field>

              <Field
                label="Min upside (%)"
                htmlFor="criteria-min-upside"
                error={validationErrors.min_upside}
                required
              >
                <Input
                  id="criteria-min-upside"
                  type="number"
                  step={0.1}
                  value={criteria.min_upside}
                  onChange={(event) => setCriterion("min_upside", event.target.value)}
                  aria-invalid={validationErrors.min_upside ? true : undefined}
                />
              </Field>

              <Field
                label="Max results"
                htmlFor="criteria-max-results"
                error={validationErrors.max_results}
                required
              >
                <Input
                  id="criteria-max-results"
                  type="number"
                  min={1}
                  max={100}
                  step={1}
                  value={criteria.max_results}
                  onChange={(event) => setCriterion("max_results", event.target.value)}
                  aria-invalid={validationErrors.max_results ? true : undefined}
                />
              </Field>
            </div>
          </section>

          <section
            aria-labelledby="assumptions-heading"
            className="rounded-xl border border-border bg-card p-6"
          >
            <h2
              id="assumptions-heading"
              className="text-title font-semibold text-foreground"
            >
              3. Valuation assumptions
            </h2>

            <p className="mt-1 text-caption text-subtle-foreground">
              These are <strong>user-provided assumptions</strong>, not market
              data. Beta and current price are prefilled from the real{" "}
              <code>/analyze</code> market snapshot when available; otherwise
              you must enter them. Rate fields use decimals (0.08 = 8%).
            </p>

            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Field
                label="Beta"
                htmlFor="assumption-beta"
                hint={
                  betaAvailable
                    ? "Prefilled from real market data."
                    : "Not available from market data — enter a value."
                }
                error={validationErrors.beta}
                required
              >
                <Input
                  id="assumption-beta"
                  type="number"
                  min={0}
                  step={0.01}
                  value={effectiveBeta}
                  disabled={betaAvailable}
                  onChange={(event) => setAssumption("beta", event.target.value)}
                  aria-invalid={validationErrors.beta ? true : undefined}
                />
              </Field>

              {!currentPriceAvailable && (
                <Field
                  label="Current price ($)"
                  htmlFor="assumption-current-price"
                  hint="Not available from market data — enter the price to use."
                  error={validationErrors.current_price}
                  required
                >
                  <Input
                    id="assumption-current-price"
                    type="number"
                    min={0}
                    step={0.01}
                    value={manualPrice}
                    onChange={(event) => setManualPrice(event.target.value)}
                    aria-invalid={validationErrors.current_price ? true : undefined}
                  />
                </Field>
              )}

              <Field
                label="FCF growth rate"
                htmlFor="assumption-growth"
                hint="Your assumption. 0.08 = 8%."
                error={validationErrors.growth_rate}
                required
              >
                <Input
                  id="assumption-growth"
                  type="number"
                  min={0}
                  max={1}
                  step={0.005}
                  value={assumptions.growth_rate}
                  onChange={(event) => setAssumption("growth_rate", event.target.value)}
                  aria-invalid={validationErrors.growth_rate ? true : undefined}
                />
              </Field>

              <Field
                label="Risk-free rate"
                htmlFor="assumption-risk-free"
                hint="Your assumption. 0.0425 = 4.25%."
                error={validationErrors.risk_free_rate}
                required
              >
                <Input
                  id="assumption-risk-free"
                  type="number"
                  min={0}
                  max={1}
                  step={0.0025}
                  value={assumptions.risk_free_rate}
                  onChange={(event) => setAssumption("risk_free_rate", event.target.value)}
                  aria-invalid={validationErrors.risk_free_rate ? true : undefined}
                />
              </Field>

              <Field
                label="Expected market return"
                htmlFor="assumption-market-return"
                hint="Your assumption. 0.10 = 10%."
                error={validationErrors.market_return}
                required
              >
                <Input
                  id="assumption-market-return"
                  type="number"
                  min={0}
                  max={1}
                  step={0.005}
                  value={assumptions.market_return}
                  onChange={(event) => setAssumption("market_return", event.target.value)}
                  aria-invalid={validationErrors.market_return ? true : undefined}
                />
              </Field>

              <Field
                label="Effective tax rate"
                htmlFor="assumption-tax"
                hint="Your assumption. 0.21 = 21%."
                error={validationErrors.tax_rate}
                required
              >
                <Input
                  id="assumption-tax"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={assumptions.tax_rate}
                  onChange={(event) => setAssumption("tax_rate", event.target.value)}
                  aria-invalid={validationErrors.tax_rate ? true : undefined}
                />
              </Field>

              <Field
                label="Cost of debt"
                htmlFor="assumption-cost-of-debt"
                hint="Backend default shown; edit if needed."
                error={validationErrors.cost_of_debt}
                required
              >
                <Input
                  id="assumption-cost-of-debt"
                  type="number"
                  min={0}
                  max={1}
                  step={0.005}
                  value={assumptions.cost_of_debt}
                  onChange={(event) => setAssumption("cost_of_debt", event.target.value)}
                  aria-invalid={validationErrors.cost_of_debt ? true : undefined}
                />
              </Field>

              <Field
                label="Terminal growth"
                htmlFor="assumption-terminal-growth"
                hint="Backend default shown; edit if needed."
                error={validationErrors.terminal_growth}
                required
              >
                <Input
                  id="assumption-terminal-growth"
                  type="number"
                  min={0}
                  max={1}
                  step={0.005}
                  value={assumptions.terminal_growth}
                  onChange={(event) => setAssumption("terminal_growth", event.target.value)}
                  aria-invalid={validationErrors.terminal_growth ? true : undefined}
                />
              </Field>

              <Field
                label="Projection years"
                htmlFor="assumption-years"
                hint="Backend default shown; edit if needed."
                error={validationErrors.years}
                required
              >
                <Input
                  id="assumption-years"
                  type="number"
                  min={1}
                  max={30}
                  step={1}
                  value={assumptions.years}
                  onChange={(event) => setAssumption("years", event.target.value)}
                  aria-invalid={validationErrors.years ? true : undefined}
                />
              </Field>
            </div>

            <div className="mt-6">
              <Button
                onClick={runCheck}
                disabled={screenMutation.isPending}
                data-testid="run-criteria-check"
              >
                {screenMutation.isPending && (
                  <Loader2
                    size={16}
                    className="motion-safe:animate-spin"
                    aria-hidden="true"
                  />
                )}
                {screenMutation.isPending
                  ? "Running check…"
                  : "Run financial criteria check"}
              </Button>
            </div>

            {screenMutation.isError && (
              <div className="mt-4">
                <ErrorInline
                  error={screenMutation.error}
                  onRetry={runCheck}
                />
              </div>
            )}
          </section>
        </>
      )}

      {/* Step 4 — result */}
      {screenResult && (
        <section
          aria-labelledby="criteria-result-heading"
          className="rounded-xl border border-border bg-card p-6"
          data-testid="criteria-result"
        >
          <h2
            id="criteria-result-heading"
            className="text-title font-semibold text-foreground"
          >
            4. Financial criteria check result
          </h2>

          <p className="mt-1 text-caption text-subtle-foreground">
            {screenResult.total === 0
              ? "The candidate did not pass the screening criteria."
              : "Calculated by the backend from the real statement data and your assumptions."}
          </p>

          {screenResult.results.length === 0 ? (
            <p
              className="mt-6 rounded-lg border border-border bg-background px-4 py-3 text-body text-subtle-foreground"
              role="status"
            >
              No result — the candidate did not meet the criteria you set.
            </p>
          ) : (
            screenResult.results.map((item: ScreenItemData) => (
              <div
                key={item.ticker}
                className="mt-6 space-y-6"
              >
                <div>
                  <h3 className="text-body font-semibold text-foreground">
                    {item.name ?? item.ticker}
                    <span className="ml-2 font-mono text-caption text-subtle-foreground">
                      {item.ticker}
                    </span>
                  </h3>
                </div>

                <div className="grid gap-6 lg:grid-cols-3">
                  <div>
                    <p className="mb-2 text-caption font-medium uppercase tracking-wide text-subtle-foreground">
                      Actual scores (backend)
                    </p>
                    <dl>
                      <DataRow label="Piotroski F-Score" value={`${item.piotroski_score}/9`} />
                      <DataRow label="Altman Z-Score" value={item.altman_score.toFixed(2)} />
                      <DataRow label="Beneish M-Score" value={item.beneish_score.toFixed(2)} />
                      <DataRow
                        label="Health"
                        value={`${item.health_score}/100 · ${item.health_rating}`}
                      />
                    </dl>
                  </div>

                  <div>
                    <p className="mb-2 text-caption font-medium uppercase tracking-wide text-subtle-foreground">
                      Calculated valuation (backend)
                    </p>
                    <dl>
                      <DataRow
                        label="Intrinsic value"
                        value={item.intrinsic_value.toFixed(2)}
                      />
                      <DataRow label="Upside" value={`${item.upside.toFixed(2)}%`} />
                      <DataRow label="Recommendation" value={item.recommendation} />
                    </dl>
                  </div>

                  <div>
                    <p className="mb-2 text-caption font-medium uppercase tracking-wide text-subtle-foreground">
                      Criteria applied (your inputs)
                    </p>
                    <dl>
                      <DataRow label="Min Piotroski" value={criteria.min_piotroski} />
                      <DataRow label="Min Altman" value={criteria.min_altman} />
                      <DataRow label="Max Beneish" value={criteria.max_beneish} />
                      <DataRow label="Min upside (%)" value={criteria.min_upside} />
                    </dl>
                  </div>
                </div>

                <div
                  className="flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-3"
                  role="status"
                >
                  {item.piotroski_score >= toNumber(criteria.min_piotroski)! &&
                  item.altman_score >= toNumber(criteria.min_altman)! &&
                  item.beneish_score <= toNumber(criteria.max_beneish)! &&
                  item.upside >= toNumber(criteria.min_upside)! ? (
                    <>
                      <CheckCircle2
                        size={18}
                        className="text-gain"
                        aria-hidden="true"
                      />
                      <span className="text-body text-foreground">
                        Candidate meets the criteria you set.
                      </span>
                    </>
                  ) : (
                    <>
                      <XCircle
                        size={18}
                        className="text-loss"
                        aria-hidden="true"
                      />
                      <span className="text-body text-foreground">
                        Candidate does not meet every criterion you set.
                      </span>
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </section>
      )}
    </div>
  );
}








