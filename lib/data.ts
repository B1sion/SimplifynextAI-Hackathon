/**
 * FIXTURE DATA — frontend only.
 *
 * Everything in this file is placeholder content lifted from the design mockup so
 * the UI can be built and demoed without a backend. Nothing here should be imported
 * by components directly; go through ./api.ts so the backend team has one place to
 * swap in real calls.
 */

import type {
  ActionCenter,
  CompassReport,
  DiscoverSummary,
  FactGroup,
  Job,
  MatchReport,
  ProfileQuestion,
  SessionSummary,
  SkillUnlock,
  StageGroup,
  Tracker,
  WatchFeed,
} from "./types";

export const STAGES: StageGroup[] = [
  {
    group: "Set up",
    items: [
      { id: "upload", label: "Upload resume", href: "/" },
      { id: "facts", label: "Check the facts", href: "/facts" },
      { id: "profile", label: "Three questions", href: "/profile" },
    ],
  },
  {
    group: "Match",
    items: [
      { id: "discover", label: "Find jobs", href: "/discover" },
      { id: "match", label: "Match report", href: "/match" },
      { id: "pass", label: "Work pass check", href: "/pass" },
      { id: "act", label: "Take action", href: "/act" },
    ],
  },
  {
    group: "Ongoing",
    items: [
      { id: "watch", label: "Overnight watch", href: "/watch" },
      { id: "track", label: "Track progress", href: "/track" },
    ],
  },
];

export const SESSION_SUMMARY: SessionSummary = {
  candidateName: "Nadia Rahman",
  factsConfirmed: 14,
  claimsBlocked: 1,
  lastWatchRun: "03:18 today",
};

export const FACTS: FactGroup[] = [
  {
    group: "Skills",
    items: [
      {
        value: "Python — pandas, Airflow",
        source: "Built ETL pipelines in Python (pandas, Airflow) processing 2M+ rows daily",
        location: "Experience · line 14",
      },
      {
        value: "SQL — Redshift, BigQuery",
        source: "Wrote 40+ production SQL queries against Redshift for the regional ops team",
        location: "Experience · line 16",
      },
      {
        value: "Tableau",
        source: "Shipped 3 Tableau dashboards used daily by 60+ operations staff",
        location: "Experience · line 17",
      },
      {
        value: "A/B testing",
        source: "Ran 2 pricing experiments, measured lift at 95% confidence",
        location: "Experience · line 19",
      },
    ],
  },
  {
    group: "Work history",
    items: [
      {
        value: "Data Analyst Intern · Shopee · 6 months",
        source: "Data Analyst Intern, Shopee Singapore — Jun 2024 to Dec 2024",
        location: "Experience · line 12",
      },
      {
        value: "Research Assistant · NUS · 8 months",
        source: "Research Assistant, NUS Business Analytics Centre — Aug 2023 to Apr 2024",
        location: "Experience · line 22",
      },
    ],
  },
  {
    group: "Education",
    items: [
      {
        value: "BEng Industrial & Systems Engineering",
        source: "BEng Industrial & Systems Engineering, National University of Singapore, 2025",
        location: "Education · line 5",
      },
    ],
  },
];

export const PROFILE_QUESTIONS: ProfileQuestion[] = [
  {
    id: "work-status",
    question: "What is your work status in Singapore?",
    options: ["Citizen or PR", "Needs an Employment Pass", "On a student pass"],
    defaultPick: 1,
  },
  {
    id: "qualification",
    question: "Highest completed qualification",
    options: ["Diploma", "Bachelor's", "Master's or above"],
    defaultPick: 1,
  },
  {
    id: "experience",
    question: "Years of full-time work experience",
    options: ["Under 1", "1 to 3", "3 to 5", "5 or more"],
    defaultPick: 0,
  },
];

export const UNLOCKS: SkillUnlock[] = [
  { name: "Amplitude", jobs: 43, weeks: "3 weeks", pct: 100 },
  { name: "dbt", jobs: 27, weeks: "6 weeks", pct: 63 },
  { name: "Looker", jobs: 18, weeks: "2 weeks", pct: 42 },
];

export const DISCOVER_SUMMARY: DiscoverSummary = {
  totalRoles: 2847,
  canApply: 24,
  mightNotQualify: 61,
  cannotApply: 19,
};

export const JOBS: Job[] = [
  { id: "grab-data-analyst", title: "Data Analyst", company: "Grab", location: "Singapore · Hybrid", score: 9, verdict: "v", verdictLabel: "Can apply" },
  { id: "sea-analytics-associate", title: "Analytics Associate", company: "Sea Group", location: "Singapore · On-site", score: 8, verdict: "v", verdictLabel: "Can apply" },
  { id: "shopee-product-analyst", title: "Product Analyst", company: "Shopee", location: "Singapore · Hybrid", score: 7, verdict: "c", verdictLabel: "Might not qualify" },
  { id: "ninjavan-operations-analyst", title: "Operations Analyst", company: "Ninja Van", location: "Singapore · On-site", score: 7, verdict: "v", verdictLabel: "Can apply" },
  { id: "dbs-junior-data-scientist", title: "Junior Data Scientist", company: "DBS", location: "Singapore · Hybrid", score: 6, verdict: "c", verdictLabel: "Might not qualify" },
  { id: "circles-bi-analyst", title: "BI Analyst", company: "Circles.Life", location: "Singapore · Remote", score: 6, verdict: "c", verdictLabel: "Might not qualify" },
  { id: "govtech-business-analyst", title: "Business Analyst", company: "GovTech", location: "Singapore · On-site", score: 5, verdict: "b", verdictLabel: "Cannot apply" },
  { id: "grab-data-engineer", title: "Data Engineer I", company: "Grab", location: "Singapore · Hybrid", score: 4, verdict: "b", verdictLabel: "Cannot apply" },
];

export const MATCH_REPORT: MatchReport = {
  jobId: "shopee-product-analyst",
  jobTitle: "Product Analyst",
  company: "Shopee",
  location: "Singapore",
  verdict: "c",
  verdictLabel: "Might not qualify",
  agents: [
    { name: "Parser", ok: true, detail: "Read 1 resume, stored 14 facts with source lines" },
    { name: "Ranker", ok: true, detail: "Scanned 2,847 postings, shortlisted 104" },
    { name: "Checker", ok: true, detail: "Split this JD into 10 requirements, tested each against your facts" },
    { name: "Writer", ok: true, detail: "Drafted 4 rewritten bullets" },
    { name: "Validator", ok: false, detail: "Blocked 1 claim with no supporting line" },
    { name: "Browser", ok: true, detail: "Found 3 likely contacts on the hiring team" },
  ],
  requirements: [
    { met: true, text: "Bachelor's degree in a quantitative discipline", evidence: "BEng Industrial & Systems Engineering, National University of Singapore, 2025", location: "Education · line 5" },
    { met: true, text: "Strong SQL — able to write queries without support", evidence: "Wrote 40+ production SQL queries against Redshift for the regional ops team", location: "Experience · line 16" },
    { met: true, text: "Python for data analysis", evidence: "Built ETL pipelines in Python (pandas, Airflow) processing 2M+ rows daily", location: "Experience · line 14" },
    { met: true, text: "Dashboarding in Tableau, Looker or similar", evidence: "Shipped 3 Tableau dashboards used daily by 60+ operations staff", location: "Experience · line 17" },
    { met: true, text: "Comfortable presenting to non-technical stakeholders", evidence: "Presented weekly findings to three regional operations leads", location: "Experience · line 18" },
    { met: true, text: "Exposure to experimentation and A/B testing", evidence: "Ran 2 pricing experiments, measured lift at 95% confidence", location: "Experience · line 19" },
    { met: true, text: "0 to 2 years of experience — fresh graduates welcome", evidence: "Data Analyst Intern, Shopee Singapore — Jun 2024 to Dec 2024", location: "Experience · line 12" },
    { met: false, text: "Hands-on with Amplitude or Mixpanel", note: "No line in your resume mentions product analytics tooling." },
    { met: false, text: "Familiarity with dbt or analytics engineering", note: "You have pipeline work, but nothing on transformation frameworks." },
    { met: false, text: "Reading knowledge of Bahasa Indonesia or Thai", note: "Listed as preferred, not required. Unlikely to block you." },
  ],
  workPass: {
    points: 30,
    needed: 40,
    summary:
      "Shopee cannot sponsor you for this role as advertised. The salary is S$200 below the benchmark for your age band, which costs 10 points on its own.",
  },
};

export const COMPASS_REPORT: CompassReport = {
  jobId: "shopee-product-analyst",
  jobTitle: "Product Analyst",
  company: "Shopee",
  location: "Singapore",
  needed: 40,
  criteria: [
    { code: "C1", name: "Salary against the sector benchmark", detail: "This role advertises S$5,400. The 2026 benchmark for your age band in information and communications is S$5,600.", points: 0, verdict: "b" },
    { code: "C2", name: "Qualifications", detail: "NUS is on the recognised institution list, so your degree scores the standard award rather than the top band.", points: 10, verdict: "c" },
    { code: "C3", name: "Diversity of the employer's workforce", detail: "Your nationality makes up under 5% of Shopee's professional headcount in Singapore.", points: 20, verdict: "v" },
    { code: "C4", name: "Support for local employment", detail: "Shopee's share of local professionals sits at or above the industry median.", points: 10, verdict: "c" },
    { code: "C5", name: "Skills bonus", detail: "Product analytics appears on the Shortage Occupation List. You do not currently meet it — this is the same gap costing you the match score.", points: 0, verdict: "b" },
    { code: "C6", name: "Strategic economic priorities", detail: "Shopee does not hold a qualifying agreement with a Singapore government agency.", points: 0, verdict: "b" },
  ],
  closingTheGap:
    "You need 10 more points, and there are two realistic routes. Negotiating to S$5,600 recovers C1 in one step, and the role is advertised only S$200 below it. Alternatively, learning Amplitude puts you on the Shortage Occupation List and earns the C5 bonus — which is the same skill already blocking three of your ten requirements.",
  disclaimer:
    "Scores are estimated from published criteria and the employer data we can see. Confirm anything you rely on against the Ministry of Manpower self-assessment tool.",
};

export const ACTION_CENTER: ActionCenter = {
  jobId: "shopee-product-analyst",
  jobTitle: "Product Analyst",
  company: "Shopee",
  met: 7,
  total: 10,
  blocked: {
    proposed: "Led a team of 5 analysts and owned regional pricing strategy end to end.",
    reason:
      "No confirmed fact supports leading a team or owning a strategy. Your resume describes a six-month individual-contributor internship. The claim was discarded before you saw it as an option, because it is the kind of line that collapses in the first interview.",
    kept: "Analysed 2M+ rows daily for three regional operations leads using SQL and Python.",
  },
  diffs: [
    {
      current: "Worked on data pipelines and made dashboards for the operations team.",
      rewritten: "Built Python ETL pipelines (pandas, Airflow) moving 2M+ rows daily, feeding 3 Tableau dashboards used by 60+ operations staff.",
      why: "Pulls the volume and headcount from Experience line 14 and 17 — both already in your resume.",
    },
    {
      current: "Helped with pricing analysis and reported to managers.",
      rewritten: "Ran two pricing experiments end to end, sizing lift at 95% confidence and presenting results weekly to three regional ops leads.",
      why: "The JD asks for experimentation. Your line 19 already proves it; this just says so plainly.",
    },
    {
      current: "Proficient in SQL, Python, Excel, Tableau, PowerPoint, Word.",
      rewritten: "SQL (Redshift, BigQuery) · Python (pandas, Airflow) · Tableau · experiment design",
      why: "Dropped Word and PowerPoint. They add nothing and dilute the four skills the JD actually screens on.",
    },
  ],
  skills: [
    {
      name: "Amplitude",
      jobs: 43,
      pay: "+S$700 median",
      weeks: "≈ 3 weeks",
      where: "Amplitude Academy — free certification track, roughly 9 hours of video plus a sandbox project.",
      note: "The single missing requirement blocking the most roles in your shortlist. It also sits on the Shortage Occupation List, which would add 10 COMPASS points.",
    },
    {
      name: "dbt",
      jobs: 27,
      pay: "+S$1,100 median",
      weeks: "≈ 6 weeks",
      where: "dbt Fundamentals (free), then rebuild one of your existing Airflow pipelines as dbt models.",
      note: "Also moves you toward analytics engineering titles, which pay above analyst bands.",
    },
    {
      name: "Looker",
      jobs: 18,
      pay: "+S$400 median",
      weeks: "≈ 2 weeks",
      where: "Google Cloud Skills Boost — LookML basics. Your Tableau background transfers most of the way.",
      note: "Lowest effort of the three. Worth doing before the Shopee interview.",
    },
  ],
  interview: [
    {
      question: "Walk me through a dashboard you built and who used it.",
      answer:
        "At Shopee I built three Tableau dashboards that 60+ operations staff used daily. I worked with the regional operations leads to pin down what they needed to see each morning, then built the queries and visualisations myself. The dashboards covered order volume and delivery exceptions, and I iterated on them for about a month based on their feedback.",
      use: "The 3 Tableau dashboards for 60+ ops staff — lead with who acted on it, not how you built it.",
    },
    {
      question: "Tell me about a time your analysis changed a decision.",
      answer:
        "I ran two pricing experiments end to end during my Shopee internship. In one, I designed the test, tracked the results in Python, and found a lift with 95% confidence. I presented that to the operations leads, and the pricing change was rolled out to the full region afterwards.",
      use: "The pricing experiment. You have the 95% confidence figure; name the decision that followed.",
    },
    {
      question: "How would you measure success for a new checkout flow?",
      answer:
        "I would start with the guardrail metric — completed orders and cancellation rate, so we know we are not hurting the core flow. The primary metric would be checkout completion rate. I would also watch time-to-complete and payment error rate as secondary signals, and cut everything by device and payment method, because those segments usually behave differently.",
      use: "No resume line covers this. Prepare a framework answer: guardrail metric, primary metric, segment cut.",
    },
    {
      question: "You have no Amplitude experience. How would you ramp up?",
      answer:
        "That is right — I have not used Amplitude yet. What I have done is heavy Tableau work at Shopee, and the concepts map across: event tracking, funnels, cohort views. I have started the Amplitude certification this month and am rebuilding one of my old Shopee analyses in Amplitude to get hands-on practice before any interview.",
      use: "Expect this — it is one of your three gaps. Say what you have done in Tableau and how the concepts map.",
    },
    {
      question: "Why product analytics rather than general BI?",
      answer:
        "My Shopee internship was ops-facing, so I have seen how data drives day-to-day operations decisions. What draws me to product analytics is working closer to the product itself — understanding how users behave and why. The skills I built — Python pipelines, dashboards, experiment analysis — carry over directly, and this role is the natural next step toward that.",
      use: "Your Shopee internship was ops-facing. Bridge it honestly rather than overclaiming product exposure.",
    },
  ],
  recruiters: [
    { name: "Denise Koh", role: "Talent Acquisition, Product & Data", why: "Posted this role 4 days ago" },
    { name: "Marcus Lee", role: "Senior Recruiter, Tech Hiring", why: "Hired for 6 analyst roles this year" },
    { name: "Priya Nair", role: "Analytics Manager", why: "Likely the hiring manager for this team" },
  ],
  draft: `Hi Denise,

I saw the Product Analyst opening and wanted to reach out directly.

I spent six months as a data analyst intern at Shopee, where I built Python pipelines handling around 2M rows a day and shipped three Tableau dashboards that 60+ operations staff used daily. I also ran two pricing experiments end to end.

I know the role asks for Amplitude, which I have not used yet — I have started working through their certification this month.

Would you be open to a short call?

Nadia`,
};

export const WATCH_FEED: WatchFeed = {
  ranAt: "03:18 this morning",
  postingsScanned: 2847,
  scope: "analyst roles in Singapore",
  enabled: true,
  events: [
    { time: "03:12", title: "4 new postings matched your saved facts", body: "Two are stronger than anything currently in your shortlist. Analytics Associate at Carousell meets 9 of 10 and clears the pass threshold on salary." },
    { time: "03:14", title: "Grab Data Analyst moved from 9 to 10 of 10", body: "The posting was edited overnight — the Looker requirement was dropped. Nothing about your profile changed." },
    { time: "03:15", title: "Circles.Life BI Analyst closed", body: "Removed from your list. You applied on 18 Aug and never heard back; the listing is now gone." },
    { time: "03:16", title: "Salary benchmark updated for your age band", body: "The information and communications benchmark rose to S$5,600. Two roles you were watching now sit below it, including Shopee." },
    { time: "03:18", title: "One thing worth doing today", body: "Three of the four new postings ask for Amplitude. It is now blocking 43 roles rather than 39." },
  ],
};

export const TRACKER: Tracker = {
  metrics: [
    { value: "5", label: "applications sent" },
    { value: "2", label: "recruiter replies" },
    { value: "6.2 → 8.1", label: "average requirements met" },
    { value: "7", label: "unsponsorable roles skipped" },
  ],
  applications: [
    { id: "app-1", job: "Product Analyst", company: "Shopee", sent: "2 Sep", status: "Applied", verdict: "v" },
    { id: "app-2", job: "Data Analyst", company: "Grab", sent: "29 Aug", status: "Recruiter replied", verdict: "v" },
    { id: "app-3", job: "Analytics Associate", company: "Sea Group", sent: "27 Aug", status: "Awaiting reply", verdict: "c" },
    { id: "app-4", job: "Operations Analyst", company: "Ninja Van", sent: "22 Aug", status: "Interview booked", verdict: "v" },
    { id: "app-5", job: "BI Analyst", company: "Circles.Life", sent: "18 Aug", status: "Listing closed", verdict: "b" },
  ],
};
