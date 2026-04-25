"use client";
import Image from "next/image";
import { Inter } from "next/font/google";
import {
  Bell,
  CircleHelp,
  GraduationCap,
  ChartNoAxesColumn,
  Bot,
  Settings,
  ShieldCheck,
  Zap,
  MessageSquare,
  Lock,
  Lightbulb,
} from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

const checklist = [
  {
    step: "check",
    title: "Upload Your Resume",
    description: "Our parser has already extracted your key technical skills.",
    state: "done",
  },
  {
    step: "2",
    title: "Connect LinkedIn",
    description:
      "Syncing with LinkedIn helps us understand your professional network and endorsements.",
    state: "active",
  },
  {
    step: "3",
    title: "Define Preferences",
    description: "Tell us about your ideal salary, location, and work-life balance.",
    state: "locked",
  },
];

const tips = [
  {
    icon: "verified_user",
    title: "Be Precise.",
    copy: "Detailed job titles help our AI filter out noise.",
  },
  {
    icon: "bolt",
    title: "Stay Active.",
    copy: "Checking your progress weekly keeps the algorithm fresh.",
  },
  {
    icon: "forum",
    title: "Ask AI.",
    copy: "Use the assistant in the sidebar for resume feedback anytime.",
  },
];

export default function OnboardingPage() {
  return (
    <div className={`${inter.className} min-h-screen bg-[#f5faf8] text-[#171d1c]`}>
      <header className="fixed top-0 z-50 flex h-12 w-full items-center justify-between border-b border-[0.5px] border-slate-300 bg-slate-50 px-4">
        <div className="text-[31px] leading-none font-bold text-teal-600 scale-[0.42] origin-left">CareerPath</div>
        <div className="hidden h-12 items-center gap-4 md:flex">
          <a className="flex h-12 items-center border-b border-[0.5px] border-teal-600 px-2 text-[14px] text-teal-600" href="#">Guides</a>
          <a className="flex h-12 items-center px-2 text-[14px] text-slate-500" href="#">Progress</a>
          <a className="flex h-12 items-center px-2 text-[14px] text-slate-500" href="#">Resources</a>
        </div>
        <div className="flex items-center gap-2.5 text-teal-600">
          <Bell size={16} />
          <CircleHelp size={16} />
          <Image
            alt="Candidate profile avatar"
            className="rounded-full border border-[0.5px] border-[#bcc9c6] object-cover"
            height={28}
            width={28}
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuDq6GTX_2lA_N76JsyV96gkpK2SuUT-gLOhzFNUqEOR2fsX3z_ppXSm9btFgPyPuX3b9jN7cEMLWHQzSqhRbihOYL65qNsEb2XN2ot79i_RurDMKeJTwWim4GOOkBM9KsUbA7ba_Bkjgez6OIRi47piWsO51Tqc0hlftLW0HeTcwLwZXBzBT4soWZ2xZAktG5CDJsL9vAQrFy-Rq8F4bIfDMRMb87Jk7I_InjUeaoGSrRYBwOxKX_FI1k2I6Yf9SxRHHDhP2m3U45WB"
          />
        </div>
      </header>

      <div className="flex min-h-screen pt-12">
        <aside className="hidden h-[calc(100vh-48px)] w-64 flex-col border-r border-[0.5px] border-slate-300 bg-slate-50 p-3 md:flex">
          <div className="mb-4 border-b border-[0.5px] border-slate-200 pb-3">
            <div className="mb-2 flex items-center gap-2">
              <Image
                alt="Candidate profile"
                className="rounded border border-[0.5px] border-[#bcc9c6] object-cover"
                height={32}
                width={32}
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuA-wZB5URqQVLHL-ov4QKGuBmMRmJmBnO2JIyA0wcw1OHQss1eBJWWrjt9YTpvG4keEOQcx-BIBDMiJFaLcYBNf-0yvxCk0rziHRKyjpV2MxAT6eOs2FToC9wKNLjTmelontOv5A2f_TcpBiTyrBFuv-_TsvAsJfHcIBjFA90W83kqlqeWnSdXZlO_Yd73t5jcKKhUTIcUxCf-rHTqqGGDrw3O0eDVBZ04027zVP5JxehtlBbIHlsPCig0PQbDqbTUxQAgio87OrY5z"
              />
              <div>
                <p className="text-[14px] font-black text-slate-900">Welcome, Alex</p>
                <p className="text-[13px] text-slate-600">Next step: Interview Prep</p>
              </div>
            </div>
            <button className="h-[33px] w-full rounded border border-[0.5px] border-[#00685f] bg-[#00685f] px-3 text-[12px] font-medium text-white">
              Resume Builder
            </button>
          </div>

          <nav className="space-y-1">
            <a className="flex items-center gap-2 border-l-2 border-teal-600 bg-slate-100 p-2 text-[13px] font-bold text-teal-600" href="#">
              <GraduationCap size={16} className="mt-px" />
              <span>Onboarding</span>
            </a>
            <a className="flex items-center gap-2 p-2 text-[13px] text-slate-600" href="#">
              <ChartNoAxesColumn size={16} />
              <span>Career Tracker</span>
            </a>
            <a className="flex items-center gap-2 p-2 text-[13px] text-slate-600" href="#">
              <Bot size={16} />
              <span>AI Assistant</span>
            </a>
            <a className="flex items-center gap-2 p-2 text-[13px] text-slate-600" href="#">
              <Settings size={16} />
              <span>Settings</span>
            </a>
          </nav>
        </aside>

        <main className="flex-1 p-3">
          <section className="mb-3">
            <h1 className="text-[47px] leading-[0.95] font-medium text-[#00685f]">
              {"Let's build your future, together."}
            </h1>
            <p className="mt-1 text-[14px] leading-[1.35] text-[#3d4947]">
              We&apos;re so glad you&apos;re here! This guide will help you set up your profile so our AI can find the perfect
              career matches for your unique skills and goals.
            </p>
          </section>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-[minmax(0,2.25fr)_minmax(0,1fr)]">
            <div className="space-y-3">
              <div className="rounded-lg border border-[0.5px] border-[#bcc9c6] bg-white p-[11px]">
                <div className="mb-3 flex items-end justify-between">
                  <div>
                    <h2 className="text-[16px] leading-[1.28] font-normal tracking-[-0.01em]">Your Quick Start Checklist</h2>
                    <p className="text-[13px] leading-[1.32] text-[#3d4947]">
                      Complete these 3 steps to unlock your first set of recommendations.
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] font-bold tracking-[0.02em] text-[#00685f]">33% COMPLETE</span>
                    <div className="mt-1 h-1 w-[104px] rounded-full bg-[#e4e9e7]">
                      <div className="h-full w-1/3 rounded-full bg-[#00685f]" />
                    </div>
                  </div>
                </div>

                <div className="space-y-[10px]">
                  {checklist.map((item) => (
                    <div
                      key={item.title}
                      className={`relative flex items-start gap-3 rounded border border-[0.5px] border-[#bcc9c6] px-3 py-[11px] ${
                        item.state === "done" ? "bg-[#f0f5f2]" : "bg-white"
                      } ${item.state === "active" ? "border-l-2 border-l-[#D97706]" : ""}`}
                    >
                      <div
                        className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                          item.state === "done"
                            ? "bg-[#00685f] text-white"
                            : item.state === "active"
                              ? "border-2 border-[#00685f] text-[#00685f]"
                              : "border border-[#bcc9c6] text-[#6d7a77]"
                        }`}
                      >
                        <span className="text-[12px] leading-none font-medium">{item.step}</span>
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="mb-1 flex items-start justify-between gap-2">
                          <h3 className={`text-[12px] font-medium ${item.state === "done" ? "line-through opacity-60" : ""}`}>
                            {item.title}
                          </h3>
                          {item.state === "active" ? (
                            <span className="rounded bg-[#9e41f51a] px-2 py-[3px] text-[11px] leading-none tracking-[0.02em] text-[#831ada]">
                              RECOMMENDED
                            </span>
                          ) : null}
                        </div>
                        <p className="text-[13px] leading-[1.32] text-[#3d4947]">{item.description}</p>
                        {item.state === "active" ? (
                          <button className="mt-2 h-8 rounded border border-[0.5px] border-[#00685f] bg-[#00685f] px-4 text-[12px] font-medium text-white">
                            Start Connection
                          </button>
                        ) : null}
                      </div>

                      {item.state === "locked" ? (
                        <Lock size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#bcc9c6]" />
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-3 rounded-lg border border-[0.5px] border-[#bcc9c6] bg-[#f0dbff] px-4 py-[11px]">
                <Lightbulb size={22} className="text-[#2c0051]" />
                <div>
                  <p className="text-[16px] font-medium leading-6 text-[#2c0051]">Did you know?</p>
                  <p className="text-[13px] leading-[1.32] text-[#2c0051]">
                    Alex, profiles that include specific industry preferences are 2x more likely to land an interview within the
                    first 30 days.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="rounded-lg border border-[0.5px] border-[#bcc9c6] bg-[#eaefed] p-[11px]">
                <h2 className="mb-2 text-[11px] uppercase tracking-[0.12em] text-[#3d4947]">Top Tips for Success</h2>
                <ul className="space-y-[10px]">
                  {tips.map((tip) => (
                    <li key={tip.title} className="flex gap-2">
                      <span className="mt-0.5 shrink-0 text-[#00685f]">
                        {tip.icon === "verified_user" ? <ShieldCheck size={14} /> : null}
                        {tip.icon === "bolt" ? <Zap size={14} /> : null}
                        {tip.icon === "forum" ? <MessageSquare size={14} /> : null}
                      </span>
                      <p className="text-[12px] leading-[1.32] text-[#171d1c]">
                        <span className="font-bold">{tip.title}</span> {tip.copy}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-lg border border-[0.5px] border-[#bcc9c6] bg-white px-3 py-[11px] text-center">
                <p className="mb-1 text-[11px] uppercase tracking-[0.04em] text-[#6d7a77]">Platform Impact</p>
                <p className="text-[40px] leading-none font-black text-[#0051d5]">4.8k+</p>
                <p className="mx-auto mt-1 max-w-[220px] text-[13px] leading-[1.32] text-[#3d4947]">
                  Professionals placed this month using CareerPath Guides.
                </p>
              </div>

              <div className="rounded-lg border border-[0.5px] border-[#bcc9c6] bg-white p-[11px]">
                <h3 className="text-[16px] font-medium">Stuck?</h3>
                <p className="mt-1 mb-[11px] text-[13px] leading-[1.32] text-[#3d4947]">
                  Our career coaches are available for a 15-min chat.
                </p>
                <button className="h-8 w-full rounded border border-[0.5px] border-[#0051d5] text-[12px] font-medium text-[#0051d5]">
                  Schedule Intro Call
                </button>
              </div>
            </div>
          </div>

          <section className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="relative h-24 overflow-hidden rounded-lg border border-[0.5px] border-[#bcc9c6]">
              <Image
                alt="Modern office space"
                className="object-cover"
                fill
                sizes="(max-width: 768px) 100vw, 33vw"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuDIV4VOQPqkBCbG3yl7vnEEA843LFRXHt4N2tN-hfAKtUaKKt68n8s4Wv6k9Jz1sOLEkEielfeEV_6iYhWS_zriEDvqZKF8GKtyYV-uepcmEOe35IPJmqkLsxmSqo7rd0u_ffsVms9Y_DffpE-a4I1ki-J2Bi2gWyjWtVZgnMwvIgD53BhZjdd3C5-9sxwzye7BGC16kkR6ESfCPH1rk0xHZHRSSC_A2uYs1lmcc17Z3qD49PUg1X95FSOkKRAxjG6QZkxSL6gdmnGU"
              />
              <div className="absolute inset-0 flex items-center justify-center bg-[#00685f33]">
                <span className="rounded bg-black/40 px-3 py-1 text-[12px] text-white backdrop-blur-sm">Office Culture Insights</span>
              </div>
            </div>
            <div className="relative h-24 overflow-hidden rounded-lg border border-[0.5px] border-[#bcc9c6]">
              <Image
                alt="Team collaborating"
                className="object-cover"
                fill
                sizes="(max-width: 768px) 100vw, 33vw"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuB1EWdg5xhqSkZs1kOZynhdHcvRT2UeAK1_-6OZZbF55Cc5Ty6pq3SxIgcEZOHksuAefrIAs9ZYS31rxgZmdnHLW71_OBedLWtCTf5Q5vjvnTEooWxnSSH0rBdyVXoA5vkMetHkmA32wrsKdB_hqK3ZN4Z8EM9xKtzE1rw2ww9bD6NyXS64bBqWvEOwZ4U1qMAwcY0DlFcJ37leq6vZ5xrbTKbNzqINDTzN-MyKeWqdZQQGJZ8M5Uah-sPvXVIZOP8UrCzWMZfZxLtA"
              />
              <div className="absolute inset-0 flex items-center justify-center bg-[#0051d533]">
                <span className="rounded bg-black/40 px-3 py-1 text-[12px] text-white backdrop-blur-sm">Networking Tools</span>
              </div>
            </div>
            <div className="relative h-24 overflow-hidden rounded-lg border border-[0.5px] border-[#bcc9c6]">
              <Image
                alt="Writing resume"
                className="object-cover"
                fill
                sizes="(max-width: 768px) 100vw, 33vw"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuAaXdxJisinS-4Hgtad22I1rVo2z-Xq4UTeyY_4W-TV9gRSPwveyVUFbxq1dPWf5xaD-yuTJl90dnKjqO1BUxuBPsq9FMK44XZR5sxGSob0qfOo4YHrD7lHyttlJotic0DI-v8UE5iekAS2-C5cWX47lLxk89-bf2CZyuv_2dITwvyYTw1XKVsgjCYDQF5wyWLZ8X8w9CdwdCxQfyU9sl-nU1vVrpOrPFdyBO9UYauRsf6YrW0QSpEKIEXZLDtjnI9DCcle_WO_Ml-Q"
              />
              <div className="absolute inset-0 flex items-center justify-center bg-[#9e41f533]">
                <span className="rounded bg-black/40 px-3 py-1 text-[12px] text-white backdrop-blur-sm">Skills Lab</span>
              </div>
            </div>
          </section>
        </main>
      </div>

      <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-16 items-center justify-around border-t border-[0.5px] border-slate-300 bg-slate-50 md:hidden">
        <button className="flex flex-col items-center text-teal-600">
          <GraduationCap size={18} />
          <span className="text-[10px] font-bold">Onboarding</span>
        </button>
        <button className="flex flex-col items-center text-slate-500">
          <ChartNoAxesColumn size={18} />
          <span className="text-[10px]">Tracker</span>
        </button>
        <button className="flex flex-col items-center text-slate-500">
          <Bot size={18} />
          <span className="text-[10px]">AI</span>
        </button>
        <button className="flex flex-col items-center text-slate-500">
          <Settings size={18} />
          <span className="text-[10px]">Settings</span>
        </button>
      </nav>
    </div>
  );
}
