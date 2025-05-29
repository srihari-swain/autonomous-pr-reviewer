from pydantic import BaseModel, Field
from typing import List, Dict, Any
import openai
import os
import logging

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class AnalyzeCodeInput(BaseModel):
    pr_diff: str = Field(description="The code diff to be analyzed.")

class AnalyzeCodeTool:
    name: str = "analyze_code_tool"
    description: str = "Analyzes a code diff using an LLM to summarize changes and identify potential risks."
    args_schema: type[BaseModel] = AnalyzeCodeInput

    def __call__(self, pr_diff: str) -> Dict[str, Any]:
        if not OPENAI_API_KEY:
            logger.error(f"Tool '{self.name}': OPENAI_API_KEY is not set.")
            raise ValueError("OPENAI_API_KEY environment variable is not set.")

        logger.info(f"Tool '{self.name}': Analyzing PR diff.")
        if not pr_diff:
            logger.warning(f"Tool '{self.name}': No diff content to analyze.")
            return {"code_summary": "No changes to analyze.", "identified_risks": []}

        prompt = f"""You are an expert code review assistant.
Analyze the following GitHub pull request diff. Provide:
1. A concise summary of the changes (max 3-4 sentences).
2. A list of potential risks, bugs, or poor coding practices observed. If none, state 'No specific risks identified'.

Format your response clearly, for example:
Summary:
[Your summary here]

Identified Risks:
- [Risk 1]
- [Risk 2]

--- BEGIN DIFF ---
{pr_diff}
--- END DIFF ---
"""
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800, temperature=0.3
            )
            analysis_text = response.choices[0].message.content.strip()

            summary = "Could not parse summary."
            risks = []
            if "Summary:" in analysis_text and "Identified Risks:" in analysis_text:
                summary_part = analysis_text.split("Summary:")[1].split("Identified Risks:")[0].strip()
                risks_part = analysis_text.split("Identified Risks:")[1].strip()
                summary = summary_part
                if risks_part.lower() != 'no specific risks identified'.lower() and risks_part:
                    risks = [r.strip().lstrip('- ') for r in risks_part.split('\n') if r.strip().lstrip('- ')]
            else:
                summary = analysis_text # Fallback
            
            logger.info(f"Tool '{self.name}': Analysis complete. Summary: {summary[:50]}... Risks: {len(risks)}")
            return {"code_summary": summary, "identified_risks": risks}
        except openai.APIError as e:
            logger.error(f"Tool '{self.name}': OpenAI API Error: {e}")
            return {"code_summary": f"Error analyzing code: {e}", "identified_risks": []}
        except Exception as e:
            logger.error(f"Tool '{self.name}': Unexpected error: {e}")
            return {"code_summary": f"Unexpected error: {e}", "identified_risks": []}

class GenerateCommentInput(BaseModel):
    code_summary: str = Field(description="Summary of the code changes.")
    identified_risks: List[str] = Field(description="List of identified risks or concerns.")
    pr_diff: str = Field(description="The full code diff for context.")

class GenerateCommentTool:
    name: str = "generate_comment_tool"
    description: str = "Generates a natural-language PR review comment based on code analysis."
    args_schema: type[BaseModel] = GenerateCommentInput

    def __call__(self, code_summary: str, identified_risks: List[str], pr_diff: str) -> Dict[str, str]:
        if not OPENAI_API_KEY:
            logger.error(f"Tool '{self.name}': OPENAI_API_KEY is not set.")
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
            
        logger.info(f"Tool '{self.name}': Generating review comment.")
        risks_text = "\n".join([f"- {risk}" for risk in identified_risks]) if identified_risks else "No specific risks were highlighted."
        prompt = f"""You are an expert code review assistant. Generate a PR review comment.
Based on:
1. Code Summary: {code_summary}
2. Identified Risks:
{risks_text}
3. Full Diff:
--- BEGIN DIFF ---
{pr_diff}
--- END DIFF ---

Comment should be polite, constructive, and act as a human reviewer.
Format clearly. Start with a polite opening, discuss summary/risks with suggestions, and conclude politely.
"""
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000, temperature=0.5
            )
            review_comment = response.choices[0].message.content.strip()
            logger.info(f"Tool '{self.name}': Comment generated (preview: {review_comment[:50]}...).")
            return {"generated_review_comments": review_comment}
        except openai.APIError as e:
            logger.error(f"Tool '{self.name}': OpenAI API Error: {e}")
            return {"generated_review_comments": f"Error generating comment: {e}"}
        except Exception as e:
            logger.error(f"Tool '{self.name}': Unexpected error: {e}")
            return {"generated_review_comments": f"Unexpected error: {e}"}
