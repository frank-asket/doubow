'use client'

import { useEffect, useMemo, useState } from 'react'
import { Bell, Bookmark, CheckCircle2, CircleHelp, Link2, List, Loader2, Settings, Shield, TrendingUp, X } from 'lucide-react'
import { useSearchParams } from 'next/navigation'
import { approvalsApi } from '../../lib/api'
import { useApprovalStore } from './approvalStore'
import { useApprovals } from './useApprovals'

type DraftVariant = 'base-1' | 'base-2' | 'whatif-1' | 'whatif-2' | 'whatif-3' | 'whatif-4'

type PersistedDraftState = {
  body: string
  baseSalary: number
  equityUnits: number
  signOnBonus: number
  variant: DraftVariant
}

function isDraftVariant(value: string | null): value is DraftVariant {
  return value === 'base-1'
    || value === 'base-2'
    || value === 'whatif-1'
    || value === 'whatif-2'
    || value === 'whatif-3'
    || value === 'whatif-4'
}

function storageKeyForApproval(approvalId: string) {
  return `approvals:drafts:${approvalId}`
}

function asCurrency(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function parseBaseSalary(salaryRange?: string | null) {
  if (!salaryRange) return 185000
  const numbers = Array.from(salaryRange.matchAll(/\d[\d,]*/g)).map((m) => Number(m[0].replaceAll(',', '')))
  return numbers[0] ?? 185000
}

export default function ApprovalsPage() {
  const searchParams = useSearchParams()
  const { approvals, loading, removeApproval } = useApprovalStore()
  useApprovals()

  const pending = useMemo(() => approvals.filter((item) => item.status === 'pending'), [approvals])
  const current = pending[0] ?? null
  const [draftBody, setDraftBody] = useState('')
  const [baseSalary, setBaseSalary] = useState(205000)
  const [equityUnits, setEquityUnits] = useState(600)
  const [signOnBonus, setSignOnBonus] = useState(25000)
  const [flowVariant, setFlowVariant] = useState<DraftVariant>('base-1')
  const [submitting, setSubmitting] = useState<'approve' | 'reject' | null>(null)
  const [saveToastOpen, setSaveToastOpen] = useState(false)

  const originalBase = parseBaseSalary(current?.application?.job?.salary_range)
  const targetBonus = 15
  const originalTotal = originalBase + Math.round(originalBase * targetBonus * 0.01)
  const scenarioTotal = baseSalary + signOnBonus + Math.round(equityUnits * 114.5)
  const scenarioDelta = scenarioTotal - originalTotal
  const urlVariant = searchParams.get('variant')
  const variant: DraftVariant = isDraftVariant(urlVariant) ? urlVariant : flowVariant
  const showWhatIf = variant.startsWith('whatif-')
  const showGuardrailV2 = variant !== 'base-1'
  const showCalculatorInputs = variant === 'whatif-2' || variant === 'whatif-3' || variant === 'whatif-4'
  const showSaveScenarioAction = variant === 'whatif-3' || variant === 'whatif-4'
  const showSavedToast = variant === 'whatif-4' || saveToastOpen

  useEffect(() => {
    if (!current) {
      setDraftBody('')
      setFlowVariant('base-1')
      return
    }
    const key = storageKeyForApproval(current.id)
    const fromStorage = typeof window !== 'undefined' ? window.localStorage.getItem(key) : null
    if (fromStorage) {
      try {
        const parsed = JSON.parse(fromStorage) as Partial<PersistedDraftState>
        setDraftBody(typeof parsed.body === 'string' ? parsed.body : current.draft_body)
        setBaseSalary(typeof parsed.baseSalary === 'number' ? parsed.baseSalary : 205000)
        setEquityUnits(typeof parsed.equityUnits === 'number' ? parsed.equityUnits : 600)
        setSignOnBonus(typeof parsed.signOnBonus === 'number' ? parsed.signOnBonus : 25000)
        setFlowVariant(
          parsed.variant != null && isDraftVariant(parsed.variant) ? parsed.variant : 'base-1',
        )
        return
      } catch {
        // Fall through to defaults if stored payload is invalid.
      }
    }
    setDraftBody(current.draft_body)
    setBaseSalary(205000)
    setEquityUnits(600)
    setSignOnBonus(25000)
    setFlowVariant('base-1')
  }, [current?.id])

  useEffect(() => {
    if (!saveToastOpen) return
    if (!isDraftVariant(urlVariant)) setFlowVariant('whatif-4')
    const timer = window.setTimeout(() => setSaveToastOpen(false), 2200)
    return () => window.clearTimeout(timer)
  }, [saveToastOpen, urlVariant])

  useEffect(() => {
    if (saveToastOpen || isDraftVariant(urlVariant)) return
    if (flowVariant === 'whatif-4') setFlowVariant('whatif-3')
  }, [saveToastOpen, flowVariant, urlVariant])

  useEffect(() => {
    if (!current) return
    if (typeof window === 'undefined') return
    const key = storageKeyForApproval(current.id)
    const payload: PersistedDraftState = {
      body: draftBody,
      baseSalary,
      equityUnits,
      signOnBonus,
      variant,
    }
    window.localStorage.setItem(key, JSON.stringify(payload))
  }, [current?.id, draftBody, baseSalary, equityUnits, signOnBonus, variant])

  async function submitApproval() {
    if (!current) return
    setSubmitting('approve')
    try {
      await approvalsApi.approve(current.id, draftBody)
      if (typeof window !== 'undefined') window.localStorage.removeItem(storageKeyForApproval(current.id))
      removeApproval(current.id)
    } finally {
      setSubmitting(null)
    }
  }

  async function rejectApproval() {
    if (!current) return
    setSubmitting('reject')
    try {
      await approvalsApi.reject(current.id)
      if (typeof window !== 'undefined') window.localStorage.removeItem(storageKeyForApproval(current.id))
      removeApproval(current.id)
    } finally {
      setSubmitting(null)
    }
  }

  if (loading && pending.length === 0) {
    return <div className="p-6 text-sm text-slate-500 dark:text-slate-400">Loading drafts...</div>
  }

  return (
    <div className="min-h-screen bg-[#f5faf8] text-[#171d1c] dark:bg-slate-950 dark:text-slate-100">
      {showSavedToast ? (
        <div className="fixed left-1/2 top-[17px] z-[120] flex -translate-x-1/2 items-center gap-2 rounded-md border border-white/20 bg-[#0d9488] px-4 py-3 text-sm font-medium leading-none text-white shadow-md">
          <CheckCircle2 size={17} />
          Scenario saved successfully
          <button type="button" onClick={() => setSaveToastOpen(false)} className="ml-1 inline-flex items-center opacity-80 hover:opacity-100">
            <X size={14} />
          </button>
        </div>
      ) : null}

      <main className="ml-0 flex min-h-screen flex-col md:ml-64">
        <aside className="fixed left-0 top-0 hidden h-full w-64 border-r border-[#e2e8f0] bg-slate-50 px-4 py-4 dark:border-slate-700 dark:bg-slate-900 md:flex md:flex-col">
          <div className="mb-6 px-2">
            <p className="text-sm font-bold tracking-tight text-slate-900 dark:text-slate-100">Recruitment Ops</p>
            <p className="text-[10px] font-medium uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">High-Priority Zone</p>
          </div>
          <button className="mb-6 h-8 rounded-[4px] bg-[#00685f] text-sm font-medium text-white">+ New Draft</button>
          <nav className="space-y-1 text-[12px] font-medium uppercase tracking-[0.14em]">
            <div className="border-l-2 border-[#0d9488] bg-white dark:bg-slate-900 px-3 py-[7px] text-[#0d9488]">Drafts</div>
            <div className="px-3 py-2 text-slate-500 dark:text-slate-400">Offer Library</div>
            <div className="px-3 py-2 text-slate-500 dark:text-slate-400">Candidate Flow</div>
            <div className="px-3 py-2 text-slate-500 dark:text-slate-400">Analytics</div>
            <div className="px-3 py-2 text-slate-500 dark:text-slate-400">Workspace</div>
          </nav>
          <div className="mt-auto space-y-1 border-t border-[#e2e8f0] dark:border-slate-700 pt-4 text-[12px] font-medium uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
            <div className="px-3 py-2">Support</div>
            <div className="px-3 py-2">Archive</div>
          </div>
        </aside>

        <header className="sticky top-0 z-40 flex h-12 items-center justify-between border-b border-[#e2e8f0] dark:border-slate-700 bg-white dark:bg-slate-900 px-6">
          <div className="flex items-center gap-4">
            <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100">OfferRefine HITL</span>
            <div className="h-4 w-px bg-slate-200" />
            <h1 className="text-[12px] font-medium leading-none text-slate-800 dark:text-slate-200">
              Request Change: {current?.application?.job?.company ?? 'Google'} L5
            </h1>
          </div>
          <div className="flex items-center gap-4 text-slate-500 dark:text-slate-400">
            <Bell size={15} />
            <Settings size={15} />
            <div className="h-6 w-6 rounded-full border border-slate-200 bg-slate-100" />
          </div>
        </header>

        {!current ? (
          <section className="grid flex-1 place-items-center p-8">
            <div className="rounded-md border border-[#e2e8f0] dark:border-slate-700 bg-white dark:bg-slate-900 px-6 py-8 text-center">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-200">No pending drafts</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">New negotiation requests will appear here.</p>
            </div>
          </section>
        ) : (
          <section className="grid flex-1 grid-cols-1 gap-4 bg-[#f0f5f2] dark:bg-slate-950 p-6 lg:grid-cols-12">
            <div className="lg:col-span-8">
              <div className="flex min-h-[600px] flex-col border border-[#e2e8f0] dark:border-slate-700 bg-white dark:bg-slate-900">
                <div className="flex items-center justify-between border-b border-[#e2e8f0] bg-slate-50/50 p-2 dark:border-slate-700 dark:bg-slate-900/50">
                  <div className="flex items-center gap-1 text-slate-600 dark:text-slate-300">
                    <button type="button" className="rounded p-1.5 hover:bg-slate-100"><strong className="text-sm">B</strong></button>
                    <button type="button" className="rounded p-1.5 hover:bg-slate-100"><em className="text-sm">I</em></button>
                    <button type="button" className="rounded p-1.5 hover:bg-slate-100"><List size={14} /></button>
                    <div className="mx-1 h-4 w-px bg-slate-200" />
                    <button type="button" className="rounded p-1.5 hover:bg-slate-100"><Link2 size={14} /></button>
                  </div>
                  <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setDraftBody(current.draft_body)}
                    className="inline-flex h-8 items-center gap-1.5 border border-[#e2e8f0] dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-[12px] font-medium leading-none text-slate-600 dark:text-slate-300"
                  >
                    <CircleHelp size={12} />
                    Revert to Original
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setDraftBody((prev) => `${prev}\n\nI can also share specific Cloud Infrastructure outcomes to support this request.`)
                      if (!isDraftVariant(urlVariant)) {
                        setFlowVariant((prev) => (prev === 'base-1' ? 'base-2' : prev))
                      }
                    }}
                    className="inline-flex h-8 items-center gap-1.5 border border-[#e2e8f0] dark:border-slate-700 bg-[#6bd8cb] px-3 text-[12px] font-medium leading-none text-[#005049]"
                  >
                    <CheckCircle2 size={12} />
                    AI Refine
                  </button>
                </div>
                </div>
                <textarea
                  value={draftBody}
                  onChange={(event) => setDraftBody(event.target.value)}
                  className="min-h-[520px] flex-1 resize-none border-none px-8 py-8 text-[14px] leading-[1.48] text-slate-900 dark:text-slate-100 focus:outline-none"
                />
              </div>
            </div>

            <div className="space-y-4 lg:col-span-4">
              <div className="border border-[#e2e8f0] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
                <h3 className="mb-3 text-[12px] font-medium uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Offer Snapshot</h3>
                <div className="space-y-2 text-[13px]">
                  <div className="flex items-center justify-between border-b border-[#e2e8f0] dark:border-slate-700 pb-2"><span className="text-slate-500 dark:text-slate-400">Base Salary</span><span className="font-semibold">{asCurrency(originalBase)}</span></div>
                  <div className="flex items-center justify-between border-b border-[#e2e8f0] dark:border-slate-700 pb-2"><span className="text-slate-500 dark:text-slate-400">Equity (GSUs)</span><span className="font-semibold">450 Units</span></div>
                  <div className="flex items-center justify-between border-b border-[#e2e8f0] dark:border-slate-700 pb-2"><span className="text-slate-500 dark:text-slate-400">Target Bonus</span><span className="font-semibold">15%</span></div>
                  <div className="flex items-center justify-between pt-1"><span className="font-medium text-slate-800 dark:text-slate-200">Total Comp (Est)</span><span className="font-bold text-[#00685f]">{asCurrency(originalTotal)}</span></div>
                </div>
              </div>

              {showWhatIf ? (
                <div className="border border-[#e2e8f0] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
                  <h3 className="mb-3 text-[12px] font-medium uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">What-If Calculator</h3>
                  <div className="space-y-4">
                    <div>
                      <div className="mb-1 flex justify-between">
                        <label className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Base Salary</label>
                        {showCalculatorInputs ? (
                          <div className="flex items-center gap-1 rounded border border-[#e2e8f0] dark:border-slate-700 bg-slate-50 dark:bg-slate-900/80 px-2 py-1">
                            <span className="text-[11px] font-medium text-slate-400">$</span>
                            <input
                              value={baseSalary.toLocaleString('en-US')}
                              onChange={(e) => setBaseSalary(Number(e.target.value.replaceAll(',', '')) || 0)}
                              className="w-16 border-none bg-transparent p-0 text-right text-xs font-semibold text-slate-700 focus:outline-none"
                            />
                          </div>
                        ) : (
                        <span className="text-xs font-semibold leading-none text-slate-700">{asCurrency(baseSalary)}</span>
                        )}
                      </div>
                      <input
                        type="range"
                        min={150000}
                        max={300000}
                        step={1000}
                        value={baseSalary}
                        onChange={(e) => {
                          setBaseSalary(Number(e.target.value))
                          if (!isDraftVariant(urlVariant)) setFlowVariant((prev) => (prev === 'whatif-1' ? 'whatif-2' : prev))
                        }}
                        className="h-1 w-full cursor-pointer rounded-lg bg-slate-100 accent-[#00685f]"
                      />
                    </div>
                    <div>
                      <div className="mb-1 flex justify-between">
                        <label className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Equity (GSUs)</label>
                        {showCalculatorInputs ? (
                          <div className="flex items-center gap-1 rounded border border-[#e2e8f0] dark:border-slate-700 bg-slate-50 dark:bg-slate-900/80 px-2 py-1">
                            <input
                              value={equityUnits}
                              onChange={(e) => setEquityUnits(Number(e.target.value) || 0)}
                              className="w-8 border-none bg-transparent p-0 text-right text-xs font-semibold text-slate-700 focus:outline-none"
                            />
                            <span className="text-[11px] font-medium text-slate-400">Units</span>
                          </div>
                        ) : (
                        <span className="text-xs font-semibold leading-none text-slate-700">{equityUnits} Units</span>
                        )}
                      </div>
                      <input
                        type="range"
                        min={0}
                        max={1000}
                        step={10}
                        value={equityUnits}
                        onChange={(e) => {
                          setEquityUnits(Number(e.target.value))
                          if (!isDraftVariant(urlVariant)) setFlowVariant((prev) => (prev === 'whatif-1' ? 'whatif-2' : prev))
                        }}
                        className="h-1 w-full cursor-pointer rounded-lg bg-slate-100 accent-[#00685f]"
                      />
                    </div>
                    <div>
                      <div className="mb-1 flex justify-between">
                        <label className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Sign-on Bonus</label>
                        {showCalculatorInputs ? (
                          <div className="flex items-center gap-1 rounded border border-[#e2e8f0] dark:border-slate-700 bg-slate-50 dark:bg-slate-900/80 px-2 py-1">
                            <span className="text-[11px] font-medium text-slate-400">$</span>
                            <input
                              value={signOnBonus.toLocaleString('en-US')}
                              onChange={(e) => setSignOnBonus(Number(e.target.value.replaceAll(',', '')) || 0)}
                              className="w-14 border-none bg-transparent p-0 text-right text-xs font-semibold text-slate-700 focus:outline-none"
                            />
                          </div>
                        ) : (
                        <span className="text-xs font-semibold leading-none text-slate-700">{asCurrency(signOnBonus)}</span>
                        )}
                      </div>
                      <input
                        type="range"
                        min={0}
                        max={100000}
                        step={5000}
                        value={signOnBonus}
                        onChange={(e) => {
                          setSignOnBonus(Number(e.target.value))
                          if (!isDraftVariant(urlVariant)) setFlowVariant((prev) => (prev === 'whatif-1' ? 'whatif-2' : prev))
                        }}
                        className="h-1 w-full cursor-pointer rounded-lg bg-slate-100 accent-[#00685f]"
                      />
                    </div>
                    <div className={`${showCalculatorInputs ? 'pt-4' : 'pt-3'} border-t border-[#e2e8f0] dark:border-slate-700`}>
                      <div className={`${showCalculatorInputs ? 'mb-1.5' : 'mb-1'} flex items-center justify-between`}>
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Scenario Total</span>
                        <div className="flex items-center gap-3">
                          {showSaveScenarioAction ? (
                            <button
                              type="button"
                              onClick={() => {
                                if (!isDraftVariant(urlVariant)) setFlowVariant('whatif-3')
                                setSaveToastOpen(true)
                              }}
                              className="inline-flex items-center gap-1 border border-[#e2e8f0] dark:border-slate-700 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.1em] leading-none text-[#00685f]"
                            >
                              <Bookmark size={12} />
                              Save Scenario
                            </button>
                          ) : null}
                          <span className={`font-bold text-slate-900 dark:text-slate-100 ${showSaveScenarioAction ? 'text-lg' : 'text-[14px]'}`}>{asCurrency(scenarioTotal)}</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Delta from Original</span>
                        <span className="inline-flex items-center gap-1 text-xs font-bold leading-none text-[#00685f]">
                          <TrendingUp size={13} />
                          +{asCurrency(scenarioDelta)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}

              <div className="border border-l-2 border-l-amber-600 border-[#e2e8f0] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
                <h3 className="mb-2 text-[12px] font-medium uppercase tracking-[0.12em] text-amber-700">AI Feedback</h3>
                <p className="text-[13px] text-slate-600 dark:text-slate-300">Tone is professional, appreciative, and data-driven.</p>
                <p className="mt-2 text-[13px] text-slate-600 dark:text-slate-300">Suggestion: Highlight specific Cloud Infrastructure metrics to justify the increase.</p>
              </div>

              <div className="border border-l-2 border-l-[#0d9488] border-[#e2e8f0] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
                <h3 className="mb-3 inline-flex items-center gap-1.5 text-[12px] font-medium uppercase tracking-[0.12em] text-[#00685f]">
                  <Shield size={13} />
                  Negotiation Guardrails
                </h3>
                {showGuardrailV2 ? (
                  <div>
                    <p className="mb-4 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Market Benchmark (L5 Software Engineer)</p>
                    <div className="relative mb-6 h-12">
                      <div className="absolute bottom-4 left-0 right-0 h-px bg-slate-200" />
                      <div className="absolute bottom-3 left-0 flex flex-col items-center text-[9px] font-medium text-slate-400"><div className="mb-1 h-2 w-px bg-slate-300" />P25<span className="text-[10px] text-slate-500 dark:text-slate-400">$180k</span></div>
                      <div className="absolute bottom-3 left-[33%] flex flex-col items-center text-[9px] font-medium text-slate-400"><div className="mb-1 h-2 w-px bg-slate-300" />P50<span className="text-[10px] text-slate-500 dark:text-slate-400">$205k</span></div>
                      <div className="absolute bottom-3 left-[66%] flex flex-col items-center text-[9px] font-medium text-slate-400"><div className="mb-1 h-2 w-px bg-slate-300" />P75<span className="text-[10px] text-slate-500 dark:text-slate-400">$225k</span></div>
                      <div className="absolute bottom-3 right-0 flex flex-col items-center text-[9px] font-medium text-slate-400"><div className="mb-1 h-2 w-px bg-slate-300" />P90<span className="text-[10px] text-slate-500 dark:text-slate-400">$245k</span></div>
                      <div className="absolute bottom-4 left-[10%] right-[30%] h-1 rounded-full bg-[#0d9488]/20" />
                      <div className="absolute bottom-1 left-[15%] flex flex-col items-center">
                        <div className="mb-1 h-2 w-2 rounded-full border-2 border-white bg-slate-400 shadow-sm" />
                        <span className="whitespace-nowrap text-[9px] font-bold uppercase tracking-tight leading-none text-slate-400">Current Offer</span>
                      </div>
                      <div className="absolute bottom-1 left-[45%] flex flex-col items-center">
                        <div className="mb-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-[#0d9488] shadow-sm" />
                        <span className="whitespace-nowrap text-[9px] font-bold uppercase tracking-tight leading-none text-[#0d9488]">Target Range</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Market Benchmark (L5)</p>
                    <div className="relative h-1.5 rounded-full bg-slate-100">
                      <div className="absolute left-[30%] right-[20%] top-0 h-1.5 rounded-full bg-[#89f5e7]" />
                      <div className="absolute left-[55%] top-0 h-1.5 w-[2px] bg-[#00685f]" />
                    </div>
                    <div className="mt-1 flex items-center justify-between text-[9px] uppercase text-slate-400">
                      <span>$175k</span>
                      <span className="font-bold text-[#00685f]">Current Target</span>
                      <span>$230k</span>
                    </div>
                  </div>
                )}
                <div className="mt-3 border border-[#e2e8f0] dark:border-slate-700 bg-slate-50 dark:bg-slate-900/80 p-2">
                  <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">Recruiter Notes</p>
                  <p className="text-[11px] italic leading-[1.3] text-slate-600 dark:text-slate-300">
                    Sarah is data-centric. Responds best to external offer comparisons or internal equity parity arguments.
                  </p>
                </div>
              </div>
            </div>
          </section>
        )}

        <footer className="sticky bottom-0 z-30 flex h-14 items-center justify-between border-t border-[#e2e8f0] dark:border-slate-700 bg-white dark:bg-slate-900 px-6">
          <button type="button" onClick={() => current && setDraftBody(current.draft_body)} className="h-8 border border-[#e2e8f0] dark:border-slate-700 px-4 text-[12px] font-medium leading-none text-slate-600 dark:text-slate-300">
            Cancel
          </button>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                if (!isDraftVariant(urlVariant)) setFlowVariant('whatif-1')
              }}
              className="h-8 border border-[#e2e8f0] dark:border-slate-700 px-4 text-[12px] font-medium leading-none text-slate-600 dark:text-slate-300"
            >
              Save as Draft
            </button>
            <button type="button" onClick={() => void submitApproval()} disabled={!current || submitting !== null} className="inline-flex h-8 items-center gap-2 bg-[#00685f] px-6 text-[12px] font-semibold leading-none text-white disabled:opacity-60">
              {submitting === 'approve' ? <Loader2 size={14} className="animate-spin" /> : null}
              Send via Gmail
            </button>
            <button type="button" onClick={() => void rejectApproval()} disabled={!current || submitting !== null} className="inline-flex h-8 items-center gap-2 border border-[#e2e8f0] dark:border-slate-700 px-4 text-[12px] font-medium leading-none text-slate-700 disabled:opacity-60">
              {submitting === 'reject' ? <Loader2 size={14} className="animate-spin" /> : <X size={14} />}
              Reject
            </button>
          </div>
        </footer>
      </main>
    </div>
  )
}
