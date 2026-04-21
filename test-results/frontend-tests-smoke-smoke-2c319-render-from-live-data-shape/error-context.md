# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend/tests/smoke.spec.ts >> smoke flows >> discover flow: stats render from live data shape
- Location: frontend/tests/smoke.spec.ts:94:7

# Error details

```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
Call log:
  - navigating to "/discover", waiting until "load"

```

# Test source

```ts
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
  172 |               updated_at: now,
  173 |             },
  174 |           ],
  175 |           total: 1,
  176 |           page: 1,
  177 |           page_size: 20,
  178 |         }),
  179 |       })
  180 |     })
  181 | 
> 182 |     await page.goto('/discover')
      |                ^ Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
  183 |     await expect(page.getByRole('heading', { name: 'Discover' })).toBeVisible()
  184 | 
  185 |     await expect(page.getByText('Evaluated this week')).toBeVisible()
  186 |     await expect(page.getByText('High fit (>= 4.0)')).toBeVisible()
  187 |     await expect(page.getByText('Avg fit score')).toBeVisible()
  188 |     await expect(page.getByText('Applied')).toBeVisible()
  189 | 
  190 |     await expect(page.getByText('148')).toBeVisible()
  191 |     await expect(page.getByText('3.8')).toBeVisible()
  192 |     await expect(page.getByText('Top matches · 2 shown')).toBeVisible()
  193 |   })
  194 | })
  195 | 
```