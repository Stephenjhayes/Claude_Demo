# Review Pull Request

Perform a thorough code review of the current branch compared to main.

## Steps
1. Run `git diff main...HEAD` to see all changes
2. Check for:
   - Logic errors or bugs
   - Missing error handling
   - Security issues (SQL injection, XSS, exposed secrets)
   - Performance concerns (N+1 queries, unnecessary re-renders)
   - Missing or inadequate tests
   - Code style violations

## Output Format
Provide a structured review:
- **Summary**: 1-2 sentence overview of the changes
- **Issues Found**: List each issue with file:line reference and severity (Critical/Warning/Suggestion)
- **Positives**: What was done well
- **Recommendation**: Approve / Request Changes / Needs Discussion

Always check `npm run lint` and `npm run test` outputs before finalizing the review.
