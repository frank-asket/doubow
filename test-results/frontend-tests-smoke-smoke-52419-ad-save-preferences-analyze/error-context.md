# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend/tests/smoke.spec.ts >> smoke flows >> resume flow: upload + save preferences + analyze
- Location: frontend/tests/smoke.spec.ts:20:7

# Error details

```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
Call log:
  - navigating to "/resume", waiting until "load"

```

# Test source

```ts
  1   | import { expect, test } from '@playwright/test'
  2   | 
  3   | const mockResumeProfile = {
  4   |   parsed_profile: {
  5   |     summary: 'Backend-focused engineer with applied AI experience.',
  6   |     skills: ['Python', 'FastAPI', 'LLMs'],
  7   |     gaps: ['System design'],
  8   |   },
  9   |   preferences: {
  10  |     target_role: 'AI/ML Engineer',
  11  |     location: 'Remote / Europe',
  12  |     min_salary: 140000,
  13  |     seniority: 'Senior',
  14  |     skills: ['RAG', 'LLMs', 'Python', 'FastAPI', 'MLOps'],
  15  |   },
  16  |   file_name: 'resume.pdf',
  17  | }
  18  | 
  19  | test.describe('smoke flows', () => {
  20  |   test('resume flow: upload + save preferences + analyze', async ({ page }) => {
  21  |     let resumeUploaded = false
  22  | 
  23  |     await page.route('**/v1/me/resume', async (route) => {
  24  |       const method = route.request().method()
  25  |       if (method === 'GET') {
  26  |         if (!resumeUploaded) {
  27  |           await route.fulfill({
  28  |             status: 404,
  29  |             contentType: 'application/json',
  30  |             body: JSON.stringify({ detail: 'Resume not found' }),
  31  |           })
  32  |           return
  33  |         }
  34  |         await route.fulfill({
  35  |           status: 200,
  36  |           contentType: 'application/json',
  37  |           body: JSON.stringify(mockResumeProfile),
  38  |         })
  39  |         return
  40  |       }
  41  | 
  42  |       if (method === 'POST') {
  43  |         resumeUploaded = true
  44  |         await route.fulfill({
  45  |           status: 200,
  46  |           contentType: 'application/json',
  47  |           body: JSON.stringify(mockResumeProfile),
  48  |         })
  49  |         return
  50  |       }
  51  | 
  52  |       await route.fallback()
  53  |     })
  54  | 
  55  |     await page.route('**/v1/me/preferences', async (route) => {
  56  |       await route.fulfill({
  57  |         status: 200,
  58  |         contentType: 'application/json',
  59  |         body: JSON.stringify(mockResumeProfile.preferences),
  60  |       })
  61  |     })
  62  | 
  63  |     await page.route('**/v1/me/resume/analyze', async (route) => {
  64  |       await route.fulfill({
  65  |         status: 200,
  66  |         contentType: 'application/json',
  67  |         body: JSON.stringify({ analysis: 'Profile analysis generated for smoke test.' }),
  68  |       })
  69  |     })
  70  | 
> 71  |     await page.goto('/resume')
      |                ^ Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
  72  |     await expect(page.getByRole('heading', { name: 'My resume' })).toBeVisible()
  73  | 
  74  |     const saveButton = page.getByRole('button', { name: 'Save preferences' })
  75  |     await expect(saveButton).toBeDisabled()
  76  | 
  77  |     const fileInput = page.locator('input[type="file"]')
  78  |     await fileInput.setInputFiles({
  79  |       name: 'resume.pdf',
  80  |       mimeType: 'application/pdf',
  81  |       buffer: Buffer.from('%PDF-1.4 smoke'),
  82  |     })
  83  | 
  84  |     await expect(page.getByText('Uploaded successfully')).toBeVisible()
  85  |     await expect(saveButton).toBeEnabled()
  86  | 
  87  |     await saveButton.click()
  88  |     await expect(page.getByText('Preferences saved.')).toBeVisible()
  89  | 
  90  |     await page.getByRole('button', { name: 'Analyze with AI' }).click()
  91  |     await expect(page.getByText('Profile analysis generated for smoke test.')).toBeVisible()
  92  |   })
  93  | 
  94  |   test('discover flow: stats render from live data shape', async ({ page }) => {
  95  |     const now = new Date().toISOString()
  96  | 
  97  |     await page.route('**/v1/me/dashboard', async (route) => {
  98  |       await route.fulfill({
  99  |         status: 200,
  100 |         contentType: 'application/json',
  101 |         body: JSON.stringify({
  102 |           high_fit_count: 1,
  103 |           pipeline_count: 1,
  104 |           pending_approvals: 0,
  105 |           evaluated_this_week: 148,
  106 |           avg_fit_score: 3.8,
  107 |           applied_awaiting_reply: 1,
  108 |           total_scored_jobs: 2,
  109 |         }),
  110 |       })
  111 |     })
  112 | 
  113 |     await page.route('**/v1/jobs**', async (route) => {
  114 |       await route.fulfill({
  115 |         status: 200,
  116 |         contentType: 'application/json',
  117 |         body: JSON.stringify({
  118 |           items: [
  119 |             {
  120 |               id: 'job_1',
  121 |               title: 'AI Engineer',
  122 |               company: 'Acme Labs',
  123 |               location: 'Remote',
  124 |               url: 'https://example.com/job-1',
  125 |               discovered_at: now,
  126 |               salary_range: '$140k-$170k',
  127 |               score: {
  128 |                 fit_score: 4.2,
  129 |                 fit_reasons: ['Strong Python background'],
  130 |                 risk_flags: [],
  131 |                 dimension_scores: { tech: 4.5, culture: 3.8, seniority: 4.0, comp: 3.7, location: 4.2 },
  132 |                 channel_recommendation: 'email',
  133 |               },
  134 |             },
  135 |             {
  136 |               id: 'job_2',
  137 |               title: 'ML Platform Engineer',
  138 |               company: 'Beta Systems',
  139 |               location: 'Paris',
  140 |               url: 'https://example.com/job-2',
  141 |               discovered_at: now,
  142 |               salary_range: '$120k-$150k',
  143 |               score: {
  144 |                 fit_score: 3.4,
  145 |                 fit_reasons: ['Platform overlap'],
  146 |                 risk_flags: ['Onsite expectation'],
  147 |                 dimension_scores: { tech: 3.6, culture: 3.1, seniority: 3.3, comp: 3.2, location: 3.8 },
  148 |                 channel_recommendation: 'linkedin',
  149 |               },
  150 |             },
  151 |           ],
  152 |           total: 2,
  153 |           page: 1,
  154 |           per_page: 20,
  155 |         }),
  156 |       })
  157 |     })
  158 | 
  159 |     await page.route('**/v1/me/applications**', async (route) => {
  160 |       await route.fulfill({
  161 |         status: 200,
  162 |         contentType: 'application/json',
  163 |         body: JSON.stringify({
  164 |           items: [
  165 |             {
  166 |               id: 'app_1',
  167 |               job_id: 'job_1',
  168 |               channel: 'email',
  169 |               status: 'pending',
  170 |               job_snapshot: { title: 'AI Engineer', company: 'Acme Labs' },
  171 |               created_at: now,
```