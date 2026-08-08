"use client";

import {
  Building2,
  Globe,
  Star,
  TrendingUp,
} from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";
import { PremiumButton } from "@/components/ui/premium-button";

export function CompanyHeader() {
  return (
    <GlassCard className="p-6">

      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">

        <div className="flex items-center gap-5">

          <div
            className="
              flex
              h-16
              w-16
              items-center
              justify-center
              rounded-2xl
              bg-gradient-to-br
              from-blue-500/20
              to-indigo-500/20
            "
          >
            <Building2
              size={30}
              className="text-blue-400"
            />
          </div>

          <div>

            <div className="flex items-center gap-3">

              <h1 className="text-3xl font-bold">
                Apple Inc.
              </h1>

              <span
                className="
                  rounded-full
                  bg-emerald-500/15
                  px-3
                  py-1
                  text-sm
                  text-emerald-400
                "
              >
                AAPL
              </span>

            </div>

            <p className="mt-2 text-zinc-400">
              Consumer Electronics • NASDAQ
            </p>

          </div>

        </div>

        <div className="flex flex-wrap gap-3">

          <PremiumButton variant="secondary">
            <Star className="mr-2 h-4 w-4" />
            Watchlist
          </PremiumButton>

          <PremiumButton variant="secondary">
            <Globe className="mr-2 h-4 w-4" />
            Website
          </PremiumButton>

          <PremiumButton>
            <TrendingUp className="mr-2 h-4 w-4" />
            Analyze
          </PremiumButton>

        </div>

      </div>

      <div className="mt-8 grid grid-cols-2 gap-5 lg:grid-cols-4">

        {[
          ["Price", "$214.13"],
          ["Market Cap", "$3.2T"],
          ["P/E", "32.7"],
          ["Dividend", "0.47%"],
        ].map(([label, value]) => (
          <div
            key={label}
            className="
              rounded-2xl
              border
              border-white/5
              bg-white/5
              p-4
            "
          >
            <p className="text-sm text-zinc-500">
              {label}
            </p>

            <h3 className="mt-2 text-2xl font-bold">
              {value}
            </h3>

          </div>
        ))}

      </div>

    </GlassCard>
  );
}