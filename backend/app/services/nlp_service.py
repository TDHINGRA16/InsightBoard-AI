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


# Prompt template for task extraction
EXTRACTION_PROMPT = """You are an expert project manager analyzing a project transcript.

Extract ALL tasks, deadlines, priorities, assignees, and dependencies from the following transcript.

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
  "tasks": [
    {{
      "title": "Short task title (max 100 chars)",
      "description": "Detailed description of what needs to be done",
      "deadline": "2026-02-20T00:00:00Z or null if not specified",
      "priority": "low|medium|high|critical",
      "assignee": "Person's name or null if not specified",
      "estimated_hours": 8
    }}
  ],
  "dependencies": [
    {{
      "task_title": "Title of dependent task (must match exactly a task title above)",
      "depends_on_title": "Title of prerequisite task (must match exactly a task title above)",
      "type": "blocks"
    }}
  ]
}}

Rules for extraction:
1. Every distinct action item or deliverable should be a separate task
2. Look for keywords like "after", "before", "depends on", "blocked by", "requires" to identify dependencies
3. Priority hints: "urgent", "ASAP", "critical" = critical; "important" = high; "nice to have" = low; otherwise = medium
4. Extract dates in ISO format. Convert relative dates like "next week" to actual dates if context allows
5. estimated_hours should be a reasonable estimate based on task complexity (default: 4-8 hours)
6. Dependencies type should be "blocks" (task B cannot start until task A completes)
7. Ensure all task_title and depends_on_title in dependencies reference actual tasks from the tasks array

Transcript to analyze:
---
{transcript}
---

Remember: Return ONLY the JSON object, no explanations or markdown formatting."""


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
        try:
            # Prepare prompt with transcript
            prompt = EXTRACTION_PROMPT.format(transcript=transcript_text[:30000])

            logger.info(f"Calling Groq LLM with model: {self.model}")

            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise JSON generator. Output only valid JSON.",
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

            title = task.get("title", "").strip()
            if not title:
                continue

            # Normalize priority
            priority = task.get("priority", "medium").lower()
            if priority not in valid_priorities:
                priority = "medium"

            # Normalize estimated hours
            try:
                estimated_hours = float(task.get("estimated_hours", 4))
                if estimated_hours < 0:
                    estimated_hours = 4
            except (ValueError, TypeError):
                estimated_hours = 4

            normalized.append({
                "title": title[:500],
                "description": task.get("description", ""),
                "deadline": task.get("deadline"),
                "priority": priority,
                "assignee": task.get("assignee"),
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

            task_title = dep.get("task_title", "").strip()
            depends_on = dep.get("depends_on_title", "").strip()

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
