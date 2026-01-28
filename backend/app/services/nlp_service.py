"""
NLP service for LLM-based task extraction using Groq.
"""

import json
import re
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger

logger = get_logger(__name__)


# Prompt template for task extraction with dependency emphasis
EXTRACTION_PROMPT = '''You are an expert project manager and dependency analyzer. Your task is to extract action items and their blocking relationships from meeting transcripts.

CURRENT DATE: {current_date}

═══════════════════════════════════════════════════════════
EXTRACTION OBJECTIVES
═══════════════════════════════════════════════════════════

1. Extract ALL tasks/action items mentioned
2. Identify ALL dependency relationships (which tasks BLOCK others)
3. Convert relative dates to absolute ISO timestamps
4. Assign accurate priority levels
5. Eliminate duplicate tasks (merge if same task mentioned multiple times)
6. Preserve original assignee names exactly as mentioned

═══════════════════════════════════════════════════════════
OUTPUT FORMAT (REQUIRED - EXACT STRUCTURE)
═══════════════════════════════════════════════════════════

Return ONLY valid JSON in this EXACT format:

{{
  "tasks": [
    {{
      "title": "Short descriptive title (max 100 chars)",
      "description": "Detailed description of what needs to be done",
      "deadline": "YYYY-MM-DDTHH:MM:SSZ or null",
      "priority": "low|medium|high|critical",
      "assignee": "Exact person name mentioned or null",
      "estimated_hours": 8
    }}
  ],
  "dependencies": [
    {{
      "task_title": "Title of DEPENDENT task (the one that is BLOCKED)",
      "depends_on_title": "Title of PREREQUISITE task (must complete FIRST)",
      "type": "blocks"
    }}
  ]
}}

CRITICAL: Task titles in "dependencies" array MUST EXACTLY MATCH titles in "tasks" array.

═══════════════════════════════════════════════════════════
DEPENDENCY DETECTION RULES
═══════════════════════════════════════════════════════════

A dependency exists when Task B CANNOT START until Task A is COMPLETED.

BLOCKING PHRASES (Task A blocks Task B):

EXPLICIT BLOCKERS:
• "after A is done, B can start" → B depends_on A
• "A must be completed before B" → B depends_on A
• "B is blocked by A" → B depends_on A
• "B can't start until A finishes" → B depends_on A
• "once A is done, then B" → B depends_on A
• "B depends on A" → B depends_on A
• "A is a prerequisite for B" → B depends_on A
• "B requires A first" → B depends_on A
• "we need A before B" → B depends_on A
• "A is a hard dependency for B" → B depends_on A
• "A is a blocker" → A blocks next mentioned task

IMPLICIT BLOCKERS:
• "I'll do A, then B" → B depends_on A (sequential)
• "First A, then B" → B depends_on A
• "A needs to happen for B to work" → B depends_on A
• "without A, B won't work" → B depends_on A
• "B needs stable A" → B depends_on A
• "coordinate with X to get Y" → Y depends_on coordination task

CONDITIONAL BLOCKERS:
• "if A passes, we can do B" → B depends_on A
• "assuming A works, B is next" → B depends_on A
• "pending A approval for B" → B depends_on A

═══════════════════════════════════════════════════════════
DEPENDENCY EXAMPLES (LEARN THE PATTERN)
═══════════════════════════════════════════════════════════

Example 1: Sequential Work
Input: "Sarah will design the mockups, and once approved, John can implement them"
Output:
{{
  "tasks": [
    {{"title": "Design Mockups", "assignee": "Sarah", ...}},
    {{"title": "Implement Mockups", "assignee": "John", ...}}
  ],
  "dependencies": [
    {{
      "task_title": "Implement Mockups",
      "depends_on_title": "Design Mockups",
      "type": "blocks"
    }}
  ]
}}

Example 2: Environment Dependency
Input: "We can't deploy to production until the staging environment is stable"
Output:
{{
  "tasks": [
    {{"title": "Stabilize Staging Environment", ...}},
    {{"title": "Deploy to Production", ...}}
  ],
  "dependencies": [
    {{
      "task_title": "Deploy to Production",
      "depends_on_title": "Stabilize Staging Environment",
      "type": "blocks"
    }}
  ]
}}

Example 3: Multiple Dependencies
Input: "The API endpoint must be ready before both the frontend and the mobile app can integrate"
Output:
{{
  "tasks": [
    {{"title": "Build API Endpoint", ...}},
    {{"title": "Frontend Integration", ...}},
    {{"title": "Mobile App Integration", ...}}
  ],
  "dependencies": [
    {{
      "task_title": "Frontend Integration",
      "depends_on_title": "Build API Endpoint",
      "type": "blocks"
    }},
    {{
      "task_title": "Mobile App Integration",
      "depends_on_title": "Build API Endpoint",
      "type": "blocks"
    }}
  ]
}}

Example 4: Chain Dependencies
Input: "First we fix the bug, then run tests, then deploy"
Output:
{{
  "tasks": [
    {{"title": "Fix Bug", ...}},
    {{"title": "Run Tests", ...}},
    {{"title": "Deploy", ...}}
  ],
  "dependencies": [
    {{
      "task_title": "Run Tests",
      "depends_on_title": "Fix Bug",
      "type": "blocks"
    }},
    {{
      "task_title": "Deploy",
      "depends_on_title": "Run Tests",
      "type": "blocks"
    }}
  ]
}}

═══════════════════════════════════════════════════════════
PRIORITY MAPPING
═══════════════════════════════════════════════════════════

CRITICAL (immediate attention, blocks everything):
• "P0", "critical", "urgent", "ASAP", "emergency"
• "blocker", "showstopper", "production down"
• "top priority", "most important", "do this first"

HIGH (important, near-term deadline):
• "P1", "high priority", "important", "must have"
• "needs to be done by [near date]"
• "critical for launch/release"

MEDIUM (normal priority):
• "P2", "normal", "standard"
• No priority mentioned → default to medium
• "should do", "we need to"

LOW (backlog, long-term):
• "P3", "low", "nice to have", "when you have time"
• "backlog", "future", "eventually"
• "if we have time", "stretch goal"

═══════════════════════════════════════════════════════════
DATE CONVERSION RULES (Current Date: {current_date})
═══════════════════════════════════════════════════════════

Convert ALL relative dates to absolute ISO 8601 format:

SPECIFIC DAYS:
• "by Monday" → Next Monday 23:59:59 from current date
• "Friday EOD" → This/next Friday 23:59:59
• "Wednesday morning" → This/next Wednesday 09:00:00
• "Thursday afternoon" → This/next Thursday 15:00:00

RELATIVE PERIODS:
• "by end of day" / "EOD" / "today" → Current date 23:59:59
• "tomorrow" → Current date + 1 day at 23:59:59
• "next week" → Current date + 7 days
• "in 2 weeks" → Current date + 14 days
• "end of month" → Last day of current month 23:59:59
• "Q1/Q2/Q3/Q4" → Last day of quarter

IMPLICIT DEADLINES:
• "urgent" / "ASAP" → Current date + 1 day
• "soon" → Current date + 3 days
• No deadline mentioned → null

TIME OF DAY:
• "EOD" / "end of day" → 23:59:59
• "morning" → 09:00:00
• "afternoon" → 15:00:00
• "evening" → 18:00:00
• If no time specified → 23:59:59 (end of day)

FORMAT: Always return as "YYYY-MM-DDTHH:MM:SSZ" (UTC timezone)

═══════════════════════════════════════════════════════════
TASK TITLE GUIDELINES
═══════════════════════════════════════════════════════════

GOOD TITLES (action-oriented, specific):
✓ "Fix Database Connection Pool Issue"
✓ "Review Marketing Copy for Technical Accuracy"
✓ "Deploy API v2 to Production"
✓ "Conduct Security Audit on Payment Flow"

BAD TITLES (vague, non-actionable):
✗ "Database"
✗ "Marketing"
✗ "Fix it"
✗ "Look into something"

RULES:
• Start with action verb (Fix, Review, Deploy, Create, Investigate, etc.)
• Be specific (include what component/feature)
• Keep under 100 characters
• If task mentioned multiple times with different wording, merge into one task with best title

═══════════════════════════════════════════════════════════
DEDUPLICATION RULES
═══════════════════════════════════════════════════════════

If the same task is mentioned multiple times in the transcript:
1. Create ONLY ONE task entry
2. Use the most descriptive title
3. Combine details from all mentions into description
4. Use the EARLIEST deadline if multiple mentioned
5. Use the HIGHEST priority if multiple mentioned

Example:
Mention 1: "John, can you fix that bug?" (medium priority)
Mention 2: "John, that bug is critical, do it ASAP" (critical priority)

Output: ONE task with priority="critical", earliest deadline

═══════════════════════════════════════════════════════════
TIME ESTIMATION GUIDELINES
═══════════════════════════════════════════════════════════

If time estimate is mentioned explicitly:
• "should take 2 hours" → estimated_hours: 2
• "half a day" → estimated_hours: 4
• "full day" → estimated_hours: 8
• "couple days" → estimated_hours: 16
• "week" → estimated_hours: 40

If NOT mentioned, infer from task complexity:
• Small tasks (review, quick fix) → 2-4 hours
• Medium tasks (feature, investigation) → 8-16 hours
• Large tasks (architecture, migration) → 24-40 hours
• Critical bugs → 8-16 hours (always high effort)

═══════════════════════════════════════════════════════════
IMPLICIT INTERMEDIATE TASKS (IMPORTANT!)
═══════════════════════════════════════════════════════════

When someone says "provide X to Y" or "give X to Y by [date]", this is 
an INTERMEDIATE HANDOFF TASK that should be extracted separately.

EXAMPLES:
Input: "David, please provide a stable build to Sam by Monday morning 
        for the full regression run. That's a hard dependency."

This creates THREE tasks with TWO dependencies:
{{
  "tasks": [
    {{"title": "Fix Payment Bug", "assignee": "David", ...}},
    {{"title": "Provide Stable Build for Regression", "assignee": "David", 
      "description": "Deliver stable build to QA team", "deadline": "Monday 09:00:00", ...}},
    {{"title": "Run Full Regression Test", "assignee": "Sam", ...}}
  ],
  "dependencies": [
    {{"task_title": "Provide Stable Build for Regression", "depends_on_title": "Fix Payment Bug", "type": "blocks"}},
    {{"task_title": "Run Full Regression Test", "depends_on_title": "Provide Stable Build for Regression", "type": "blocks"}}
  ]
}}

HANDOFF PHRASES TO DETECT:
• "provide X to Y" → intermediate handoff task
• "deliver X by [date]" → explicit deliverable task
• "send X to Y" → handoff task
• "give Y the X" → handoff task  
• "That's a hard dependency" → the previous statement creates a blocker

═══════════════════════════════════════════════════════════
PRIORITY BOOST RULES (OVERRIDE DEFAULT)
═══════════════════════════════════════════════════════════

Even if priority is not explicitly stated, BOOST to HIGH when:

LAUNCH BLOCKERS:
• Task is needed "for launch" → HIGH
• Task is input to marketing/press → HIGH
• Task blocks customer-facing feature → HIGH
• "needed by Thursday EOD" for launch week → HIGH

CUSTOMER-FACING ISSUES:
• "customers are complaining" → HIGH
• "high-visibility" issues → HIGH
• "twice a week crashes" / recurring failures → HIGH
• Any production bug affecting users → HIGH

HARD DEADLINES:
• Explicit deadline within 3 days → HIGH minimum
• "no excuses" / "absolute latest" → HIGH
• "must be done by" → HIGH

DOWNGRADE TO LOW when:
• "when you have time" → LOW
• "backlog item" → LOW
• "in a couple weeks" with no urgency → LOW
• "nice to have" / "just an idea" → LOW

═══════════════════════════════════════════════════════════
SEMANTIC DEDUPLICATION (CRITICAL!)
═══════════════════════════════════════════════════════════

SAME TASK, DIFFERENT WORDS - merge into ONE task:
• "Create A/B test document" + "Document A/B test plan" = ONE task
• "Fix the bug" + "Debug the issue" + "Patch the problem" = ONE task
• "Review blog post" + "Check blog for accuracy" = ONE task

SIMILAR BUT DIFFERENT - keep as separate tasks:
• "Fix payment bug" vs "Fix shipping bug" = TWO tasks (different bugs)
• "Deploy to staging" vs "Deploy to production" = TWO tasks (different environments)

MERGE RULES:
When the same task is mentioned multiple ways:
1. Use the MOST DESCRIPTIVE title
2. Combine descriptions from all mentions
3. Use EARLIEST deadline
4. Use HIGHEST priority
5. Keep same assignee (should be consistent)
6. Average the time estimates

═══════════════════════════════════════════════════════════
WHAT NOT TO EXTRACT
═══════════════════════════════════════════════════════════

DO NOT create tasks for:
✗ General discussion/status updates (no action needed)
✗ Questions without assigned action
✗ Past completed work ("we already did X")
✗ Hypothetical scenarios ("if we ever need to...")
✗ Meeting scheduling ("let's meet next week")

ONLY extract actionable items with clear owners or clear intent.

═══════════════════════════════════════════════════════════
VALIDATION CHECKLIST
═══════════════════════════════════════════════════════════

Before returning JSON, verify:
□ All task titles are unique (no duplicates)
□ Similar tasks are merged (semantic deduplication)
□ Intermediate handoff tasks are captured (provide X to Y)
□ All task titles in dependencies[] exist in tasks[]
□ Hard dependencies create proper chains
□ Launch blockers have HIGH priority minimum
□ Customer-facing issues have HIGH priority minimum
□ All dates are in ISO 8601 format or null
□ All priorities are one of: low, medium, high, critical
□ All estimated_hours are positive integers
□ Dependencies form a DAG (no circular dependencies)
□ JSON is valid and parseable

═══════════════════════════════════════════════════════════
TRANSCRIPT TO ANALYZE:
═══════════════════════════════════════════════════════════

{transcript}

═══════════════════════════════════════════════════════════

Extract ALL tasks and dependencies following the rules above.

Return ONLY the JSON object. No markdown code blocks (```), no explanations, no preamble.
Start your response with {{ and end with }}.
'''

class NLPService:
    """
    NLP service for extracting tasks from transcripts using Groq LLM.
    """

    def __init__(self):
        """Initialize Groq client."""
        try:
            from groq import Groq  # type: ignore
        except Exception as e:
            raise LLMError(
                "Groq SDK is not installed. Install it with `pip install groq` "
                "or disable LLM-based extraction for local development."
            ) from e

        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def extract_tasks_and_dependencies(
        self,
        transcript_text: str,
    ) -> Dict[str, Any]:
        """
        Extract tasks and dependencies from transcript using LLM.

        Args:
            transcript_text: Raw transcript text

        Returns:
            dict: Extracted tasks and dependencies

        Raises:
            LLMError: If LLM processing fails
        """
        from datetime import datetime, timezone
        
        try:
            # Get current date for relative date calculations
            current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d (%A)")
            
            # Prepare prompt with transcript and current date
            prompt = EXTRACTION_PROMPT.format(
                transcript=transcript_text[:30000],
                current_date=current_date,
            )

            logger.info(f"Calling Groq LLM with model: {self.model}")

            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a project management expert. Extract tasks and their dependencies "
                            "from meeting transcripts. Pay special attention to blocking relationships "
                            "(when one task must be completed before another can start). "
                            "Output only valid JSON with no markdown formatting."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.1,
                max_completion_tokens=4096,
                top_p=1,
                stream=True,
            )

            response_text = ""
            for chunk in response:
                response_text += chunk.choices[0].delta.content or ""
            response_text = response_text.strip()
            logger.debug(f"LLM response length: {len(response_text)}")

            # Parse JSON from response
            result = self._parse_json_response(response_text)

            # Validate structure
            if not isinstance(result.get("tasks"), list):
                result["tasks"] = []
            if not isinstance(result.get("dependencies"), list):
                result["dependencies"] = []

            # Normalize and validate tasks
            result["tasks"] = self._normalize_tasks(result["tasks"])
            result["dependencies"] = self._normalize_dependencies(
                result["dependencies"],
                result["tasks"],
            )

            logger.info(
                f"Extracted {len(result['tasks'])} tasks and "
                f"{len(result['dependencies'])} dependencies"
            )

            return result

        except Exception as e:
            logger.error(f"LLM extraction failed: {str(e)}")
            raise LLMError(f"Failed to extract tasks: {str(e)}")

    def _parse_json_response(self, response_text: str) -> dict:
        """
        Parse JSON from LLM response, handling common issues.

        Args:
            response_text: Raw response text

        Returns:
            dict: Parsed JSON

        Raises:
            LLMError: If parsing fails
        """
        # Try direct parse first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in response
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        raise LLMError("Failed to parse JSON from LLM response")

    def _normalize_tasks(self, tasks: List[dict]) -> List[dict]:
        """
        Normalize and validate extracted tasks.

        Args:
            tasks: Raw tasks from LLM

        Returns:
            List[dict]: Normalized tasks
        """
        normalized = []
        valid_priorities = {"low", "medium", "high", "critical"}

        for task in tasks:
            if not isinstance(task, dict):
                continue

            # Handle None values safely
            raw_title = task.get("title")
            title = (raw_title or "").strip()
            if not title:
                continue

            # Normalize priority (handle None)
            raw_priority = task.get("priority")
            priority = (raw_priority or "medium").lower()
            if priority not in valid_priorities:
                priority = "medium"

            # Normalize estimated hours
            try:
                estimated_hours = float(task.get("estimated_hours") or 4)
                if estimated_hours < 0:
                    estimated_hours = 4
            except (ValueError, TypeError):
                estimated_hours = 4

            # Handle None for description and assignee
            raw_description = task.get("description")
            raw_assignee = task.get("assignee")

            normalized.append({
                "title": title[:500],
                "description": raw_description or "",
                "deadline": task.get("deadline"),
                "priority": priority,
                "assignee": raw_assignee,
                "estimated_hours": estimated_hours,
            })

        return normalized

    def _normalize_dependencies(
        self,
        dependencies: List[dict],
        tasks: List[dict],
    ) -> List[dict]:
        """
        Normalize and validate dependencies.

        Args:
            dependencies: Raw dependencies from LLM
            tasks: Normalized tasks

        Returns:
            List[dict]: Valid dependencies
        """
        # Build set of valid task titles
        valid_titles = {t["title"].lower() for t in tasks}

        normalized = []
        seen = set()

        for dep in dependencies:
            if not isinstance(dep, dict):
                continue

            # Handle None values safely
            raw_task_title = dep.get("task_title")
            raw_depends_on = dep.get("depends_on_title")
            
            task_title = (raw_task_title or "").strip()
            depends_on = (raw_depends_on or "").strip()

            # Skip if titles don't exist in tasks
            if (
                not task_title
                or not depends_on
                or task_title.lower() not in valid_titles
                or depends_on.lower() not in valid_titles
            ):
                continue

            # Skip self-dependencies
            if task_title.lower() == depends_on.lower():
                continue

            # Skip duplicates
            key = (task_title.lower(), depends_on.lower())
            if key in seen:
                continue
            seen.add(key)

            normalized.append({
                "task_title": task_title,
                "depends_on_title": depends_on,
                "type": "blocks",
            })

        return normalized

    def analyze_transcript_summary(
        self,
        transcript_text: str,
    ) -> Dict[str, Any]:
        """
        Generate a summary analysis of the transcript.

        Args:
            transcript_text: Raw transcript text

        Returns:
            dict: Summary analysis
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this project transcript and provide a brief summary:

{transcript_text[:10000]}

Return JSON with:
- project_name: Inferred project name
- summary: 2-3 sentence summary
- key_themes: List of 3-5 main themes/topics
- estimated_team_size: Estimated number of people involved
- estimated_duration_weeks: Estimated project duration""",
                    }
                ],
                temperature=0.3,
                max_completion_tokens=500,
                top_p=1,
                stream=True,
            )

            response_text = ""
            for chunk in response:
                response_text += chunk.choices[0].delta.content or ""

            return self._parse_json_response(response_text.strip())
        except Exception as e:
            logger.error(f"Summary analysis failed: {e}")
            return {
                "project_name": "Unknown Project",
                "summary": "Analysis failed",
                "key_themes": [],
            }


# Singleton instance
nlp_service = NLPService()
