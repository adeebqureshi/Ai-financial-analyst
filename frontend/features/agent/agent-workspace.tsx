"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import ReactMarkdown, { type Components } from "react-markdown";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BookOpen,
  Bot,
  Briefcase,
  CheckCircle2,
  Database,
  FileText,
  Landmark,
  LineChart,
  Loader2,
  RotateCcw,
  Scale,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { api } from "@/services/api";

import type {
  AgentToolExecution,
  ChatData,
  DocumentData,
} from "@/types/analysis";

const examplePrompts = [
  "Is Nvidia overvalued?",
  "Analyze Apple's financial health.",
  "Compare Apple and Microsoft.",
  "What are Nvidia's biggest risks according to its 10-K?",
  "Compare Nvidia and AMD using their annual reports.",
  "Build an investment thesis for Microsoft.",
];

const capabilities = [
  { icon: Landmark, label: "SEC filings" },
  { icon: BookOpen, label: "Uploaded financial documents" },
  { icon: Database, label: "Financial statements" },
  { icon: TrendingUp, label: "Market data" },
  { icon: LineChart, label: "DCF valuation" },
  { icon: ShieldCheck, label: "Financial health analysis" },
  { icon: Scale, label: "Risk analysis" },
  { icon: Briefcase, label: "Company comparison" },
  { icon: Briefcase, label: "Portfolio data" },
];

const nextSteps = [
  { label: "Company Analysis", href: "/analysis", icon: LineChart },
  { label: "Compare Companies", href: "/compare", icon: Scale },
  { label: "Generate Report", href: "/reports", icon: FileText },
  { label: "Upload Documents", href: "/research", icon: BookOpen },
  { label: "Search Knowledge Base", href: "/search", icon: Search },
];

const tickerHints: Array<[string, string]> = [
  ["apple", "AAPL"],
  ["microsoft", "MSFT"],
  ["nvidia", "NVDA"],
  ["amd", "AMD"],
  ["tesla", "TSLA"],
  ["amazon", "AMZN"],
  ["google", "GOOGL"],
  ["alphabet", "GOOGL"],
  ["meta", "META"],
  ["netflix", "NFLX"],
  ["intel", "INTC"],
  ["oracle", "ORCL"],
  ["salesforce", "CRM"],
  ["palantir", "PLTR"],
  ["berkshire", "BRK"],
  ["coca-cola", "KO"],
  ["pepsi", "PEP"],
  ["jpmorgan", "JPM"],
  ["goldman", "GS"],
  ["bank of america", "BAC"],
];

const uppercasePattern = /\b([A-Z]{2,5})\b/g;

const excludedWords = new Set([
  "AI",
  "ETF",
  "SEC",
  "CEO",
  "CFO",
  "COO",
  "GDP",
  "IPO",
  "ROE",
  "ROA",
  "EPS",
  "FED",
  "USA",
  "PDF",
  "RAG",
  "API",
  "EV",
  "EBITDA",
  "IT",
  "US",
  "UK",
  "COVID",
]);

function detectTickers(query: string): string[] {
  const found: string[] = [];

  const lower = query.toLowerCase();

  for (const [name, ticker] of tickerHints) {
    if (lower.includes(name) && !found.includes(ticker)) {
      found.push(ticker);
    }
  }

  for (const match of query.matchAll(uppercasePattern)) {
    const word = match[1];

    if (!excludedWords.has(word) && !found.includes(word)) {
      found.push(word);
    }
  }

  return found;
}

function buildTools(chat: ChatData): AgentToolExecution[] {
  const tools: AgentToolExecution[] = [];

  if (chat.tools_used && chat.tools_used.length > 0) {
    tools.push(...chat.tools_used);
  }

  const hasRetrieval = tools.some(
    (tool) => tool.tool === "Knowledge base retrieval"
  );

  if (chat.sources.length > 0 && !hasRetrieval) {
    tools.push({
      tool: "Knowledge base retrieval",
      status: "done",
      detail: `${chat.sources.length} cited source${
        chat.sources.length === 1 ? "" : "s"
      }`,
    });
  }

  return tools;
}

const markdownComponents: Components = {
  h1: (props) => (
    <h1
      {...props}
      className="mb-4 mt-8 text-2xl font-bold text-white"
    />
  ),
  h2: (props) => (
    <h2
      {...props}
      className="mb-4 mt-8 text-xl font-bold text-white"
    />
  ),
  h3: (props) => (
    <h3
      {...props}
      className="mb-3 mt-6 text-lg font-semibold text-white"
    />
  ),
  p: (props) => (
    <p {...props} className="mb-4 leading-7 text-zinc-300" />
  ),
  strong: (props) => (
    <strong {...props} className="font-semibold text-white" />
  ),
  em: (props) => (
    <em {...props} className="text-zinc-200" />
  ),
  a: (props) => (
    <a
      {...props}
      target="_blank"
      rel="noreferrer"
      className="text-blue-400 underline underline-offset-2 hover:text-blue-300"
    />
  ),
  ul: (props) => (
    <ul {...props} className="mb-4 list-disc space-y-2 pl-6" />
  ),
  ol: (props) => (
    <ol {...props} className="mb-4 list-decimal space-y-2 pl-6" />
  ),
  li: (props) => (
    <li {...props} className="leading-7 text-zinc-300" />
  ),
  blockquote: (props) => (
    <blockquote
      {...props}
      className="mb-4 border-l-2 border-blue-400/40 pl-4 text-zinc-400"
    />
  ),
  code: (props) => (
    <code
      {...props}
      className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-sm text-blue-300"
    />
  ),
  pre: (props) => (
    <pre
      {...props}
      className="mb-4 overflow-x-auto rounded-xl border border-white/10 bg-black/40 p-4 font-mono text-sm text-zinc-200"
    />
  ),
  hr: () => <hr className="my-8 border-white/10" />,
  table: (props) => (
    <div className="mb-4 overflow-x-auto">
      <table {...props} className="w-full border-collapse text-sm" />
    </div>
  ),
  th: (props) => (
    <th
      {...props}
      className="border border-white/10 px-3 py-2 text-left font-semibold text-white"
    />
  ),
  td: (props) => (
    <td
      {...props}
      className="border border-white/10 px-3 py-2 text-zinc-300"
    />
  ),
};

export function AgentWorkspace() {
  const [input, setInput] = useState("");

  const [documentId, setDocumentId] = useState<string>("");

  const [question, setQuestion] = useState("");

  const [chat, setChat] = useState<ChatData | null>(null);

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.listDocuments(),
    retry: 1,
  });

  const documents: DocumentData[] =
    documentsQuery.data?.data?.documents ?? [];

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await api.chat({
        message,
        ...(documentId ? { document_id: documentId } : {}),
      });

      return (response.data ?? null) as ChatData | null;
    },
    onSuccess: (data) => {
      setChat(data);
    },
  });

  const pending = chatMutation.isPending;

  const detected = useMemo(
    () => (question ? detectTickers(question) : []),
    [question]
  );

  const selectedDocument = documents.find(
    (doc) => doc.document_id === documentId
  );

  function runResearch(prompt: string) {
    const trimmed = prompt.trim();

    if (!trimmed || pending) return;

    setQuestion(trimmed);
    setChat(null);
    setInput("");

    chatMutation.mutate(trimmed);
  }

  function reset() {
    setQuestion("");
    setChat(null);
    setInput("");
    setDocumentId("");
    chatMutation.reset();
  }

  const tools = chat ? buildTools(chat) : [];

  const hasResult = Boolean(chat) && !pending;

  return (
    <div className="mx-auto max-w-5xl space-y-10">
      {/* Hero */}
      <section>
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-sm text-blue-300">
          <Bot size={16} />
          AI FINANCIAL RESEARCH AGENT
        </div>

        <h1 className="mt-6 text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
          Your AI Financial Research Agent
        </h1>

        <p className="mt-5 max-w-3xl text-lg leading-8 text-zinc-400">
          Analyze companies, read filings, calculate valuation, assess
          risk, and build evidence-backed investment research.
        </p>
      </section>

      {/* Input */}
      <section className="rounded-[32px] border border-white/10 bg-gradient-to-br from-[#0B1220] via-[#090B11] to-[#05060A] p-6 sm:p-8">
        <label
          htmlFor="agent-research-input"
          className="text-sm font-medium uppercase tracking-widest text-zinc-500"
        >
          What do you want to research?
        </label>

        <textarea
          id="agent-research-input"
          rows={3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              runResearch(input);
            }
          }}
          placeholder="Compare Nvidia and AMD using their latest annual reports..."
          className="mt-4 w-full resize-none rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-lg text-white outline-none placeholder:text-zinc-500 focus:border-blue-500/40"
        />

        <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-1 items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-2.5">
            <FileText size={18} className="shrink-0 text-zinc-500" />

            <label
              htmlFor="agent-document-select"
              className="sr-only"
            >
              Ground the research in a document
            </label>

            <select
              id="agent-document-select"
              value={documentId}
              onChange={(e) => setDocumentId(e.target.value)}
              disabled={documents.length === 0}
              className="flex-1 bg-transparent text-sm text-white outline-none disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="" className="bg-[#0B1220]">
                General research — use all available data
              </option>

              {documents.map((doc) => (
                <option
                  key={doc.document_id}
                  value={doc.document_id}
                  className="bg-[#0B1220]"
                >
                  {doc.filename}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => runResearch(input)}
            disabled={!input.trim() || pending}
            className="flex items-center justify-center gap-2 rounded-2xl bg-white px-8 py-3 font-medium text-black transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {pending ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                Analyze
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </div>

        {documentsQuery.isError && (
          <p className="mt-4 text-sm text-zinc-500">
            The knowledge base is currently unavailable. You can still ask
            general questions.
          </p>
        )}

        {/* Example prompts (empty state) */}
        {!question && (
          <div className="mt-8">
            <p className="text-sm font-medium uppercase tracking-widest text-zinc-500">
              Try asking
            </p>

            <div className="mt-4 flex flex-wrap gap-3">
              {examplePrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => runResearch(prompt)}
                  className="rounded-full border border-white/10 bg-white/5 px-4 py-2.5 text-left text-sm text-zinc-300 transition-all hover:border-blue-500/30 hover:bg-blue-500/10 hover:text-white"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Capabilities (empty state) */}
      {!question && (
        <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-6 sm:p-8">
          <h2 className="text-xl font-bold text-white">
            AI can research using
          </h2>

          <p className="mt-2 text-sm text-zinc-500">
            Every capability below maps to a real data source or analysis
            engine already available in this workspace.
          </p>

          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {capabilities.map((capability) => {
              const Icon = capability.icon;

              return (
                <div
                  key={capability.label}
                  className="flex items-center gap-3 rounded-2xl border border-white/5 bg-white/[0.02] px-4 py-3"
                >
                  <CheckCircle2
                    size={18}
                    className="shrink-0 text-emerald-400"
                  />

                  <span className="text-sm text-zinc-200">
                    {capability.label}
                  </span>

                  <Icon
                    size={16}
                    className="ml-auto shrink-0 text-zinc-500"
                  />
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Session */}
      {question && (
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Research request */}
          <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-6 sm:p-8">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-widest text-zinc-500">
                  Research request
                </p>

                <h2 className="mt-3 text-2xl font-semibold text-white">
                  {question}
                </h2>
              </div>

              <button
                onClick={reset}
                aria-label="Start a new research request"
                className="flex shrink-0 items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-zinc-300 transition hover:bg-white/10 hover:text-white"
              >
                <RotateCcw size={16} />
                New research
              </button>
            </div>

            {selectedDocument && (
              <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-1.5 text-sm text-blue-300">
                <BookOpen size={14} />
                Grounded in {selectedDocument.filename}
              </div>
            )}
          </div>

          {/* Pending */}
          {pending && (
            <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8">
              <div className="flex items-center gap-4">
                <Loader2
                  size={28}
                  className="animate-spin text-blue-400"
                />

                <div>
                  <h3 className="text-lg font-semibold text-white">
                    Agent is researching
                  </h3>

                  <p className="mt-1 text-sm text-zinc-500">
                    Retrieving relevant context and synthesizing a grounded
                    answer. This usually takes a few seconds.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {chatMutation.isError && (
            <div className="rounded-[32px] border border-red-500/20 bg-red-500/10 p-8">
              <h3 className="text-lg font-semibold text-white">
                Research failed
              </h3>

              <p className="mt-3 text-zinc-300">
                {chatMutation.error instanceof Error
                  ? chatMutation.error.message
                  : "Something went wrong while researching your question. Please try again."}
              </p>
            </div>
          )}

          {/* Result */}
          {hasResult && chat && (
            <div className="space-y-8">
              <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-6 sm:p-8">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-2xl bg-blue-500/10 p-3">
                      <Sparkles
                        size={20}
                        className="text-blue-400"
                      />
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold text-white">
                        Research findings
                      </h3>

                      {chat.model && (
                        <p className="mt-1 text-sm text-zinc-500">
                          {chat.model}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  <ReactMarkdown components={markdownComponents}>
                    {chat.message}
                  </ReactMarkdown>
                </div>
              </div>

              {/* Tools used — only real executions */}
              <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-6 sm:p-8">
                <h3 className="flex items-center gap-2 text-base font-semibold text-white">
                  <Database size={16} className="text-blue-400" />
                  Tools executed
                </h3>

                {tools.length > 0 ? (
                  <div className="mt-5 space-y-3">
                    {tools.map((tool) => (
                      <div
                        key={tool.tool}
                        className="flex items-start gap-3 rounded-2xl border border-white/5 bg-white/[0.02] px-4 py-3"
                      >
                        {tool.status === "done" && (
                          <CheckCircle2
                            size={18}
                            className="mt-0.5 shrink-0 text-emerald-400"
                          />
                        )}

                        {tool.status === "running" && (
                          <Loader2
                            size={18}
                            className="mt-0.5 shrink-0 animate-spin text-blue-400"
                          />
                        )}

                        {tool.status === "error" && (
                          <span className="mt-0.5 h-[18px] w-[18px] shrink-0 rounded-full bg-red-500/20 text-center text-xs font-bold text-red-400">
                            !
                          </span>
                        )}

                        {tool.status === "skipped" && (
                          <span className="mt-0.5 shrink-0 text-zinc-600">
                            •
                          </span>
                        )}

                        <div>
                          <p className="text-sm font-medium text-white">
                            {tool.tool}
                          </p>

                          {tool.detail && (
                            <p className="mt-0.5 text-sm text-zinc-500">
                              {tool.detail}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-4 text-sm text-zinc-500">
                    No financial tools were executed for this response. Ask
                    about a company, valuation or health analysis, or upload
                    documents so the agent can retrieve grounded evidence.
                  </p>
                )}
              </div>

              {/* Sources */}
              <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-6 sm:p-8">
                <h3 className="flex items-center gap-2 text-base font-semibold text-white">
                  <BookOpen size={16} className="text-violet-400" />
                  Sources
                </h3>

                {chat.sources.length > 0 ? (
                  <div className="mt-5 flex flex-wrap gap-2">
                    {chat.sources.map((source, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center gap-1.5 rounded-full border border-blue-400/20 bg-blue-500/10 px-3 py-1.5 text-xs text-blue-300"
                      >
                        <FileText size={12} />
                        {source.filename}
                        {source.page != null && ` — Page ${source.page}`}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="mt-4 text-sm text-zinc-500">
                    No document sources were cited for this response.
                  </p>
                )}
              </div>

              {/* Detected companies → deep links into analysis */}
              {detected.length > 0 && (
                <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-6 sm:p-8">
                  <h3 className="text-base font-semibold text-white">
                    Continue in Company Analysis
                  </h3>

                  <p className="mt-2 text-sm text-zinc-500">
                    The agent detected these companies in your request. Open
                    their full AI analysis workspace:
                  </p>

                  <div className="mt-5 flex flex-wrap gap-3">
                    {detected.map((ticker) => (
                      <Link
                        key={ticker}
                        href={`/analysis/${ticker}`}
                        className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium text-white transition hover:border-blue-500/30 hover:bg-blue-500/10"
                      >
                        {ticker}
                        <ArrowRight size={14} className="text-zinc-500" />
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggested next steps */}
              <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-6 sm:p-8">
                <h3 className="text-base font-semibold text-white">
                  Suggested next steps
                </h3>

                <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {nextSteps.map((step) => {
                    const Icon = step.icon;

                    return (
                      <Link
                        key={step.label}
                        href={step.href}
                        className="flex items-center gap-3 rounded-2xl border border-white/5 bg-white/[0.02] px-4 py-3 transition hover:border-blue-500/30 hover:bg-white/[0.05]"
                      >
                        <Icon
                          size={18}
                          className="shrink-0 text-blue-400"
                        />

                        <span className="text-sm text-zinc-200">
                          {step.label}
                        </span>

                        <ArrowRight
                          size={14}
                          className="ml-auto shrink-0 text-zinc-600"
                        />
                      </Link>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </motion.section>
      )}
    </div>
  );
}
