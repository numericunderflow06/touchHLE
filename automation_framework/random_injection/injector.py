"""
Random Idea Injector for touchHLE Research Pipeline

Provides random suggestions to inject into prompts, potentially helping
models discover new investigation angles.
"""

import json
import random
from pathlib import Path
from typing import Optional, Literal, Dict, Any, List


class RandomIdeaInjector:
    """
    Injects randomly-selected suggestions into research pipeline prompts.

    Usage:
        injector = RandomIdeaInjector(seed=42)  # Optional seed for reproducibility

        # For code-focused pipeline (Step 2: Solution Plan)
        code_suggestion = injector.get_code_injection()

        # For error-focused pipeline (Step 2: Solution Plan)
        debug_suggestion = injector.get_debug_injection()

        # For debate rounds
        debate_suggestion = injector.get_debate_injection(pipeline="code")
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the injector.

        Args:
            seed: Optional random seed for reproducible selections.
                  If None, uses system randomness.
        """
        self.rng = random.Random(seed)
        self.seed = seed
        self._code_items = None
        self._debug_items = None
        self._base_path = Path(__file__).parent

    @property
    def code_items(self) -> List[Dict[str, Any]]:
        """Lazily load code components list."""
        if self._code_items is None:
            self._code_items = self._load_list("CODE_COMPONENTS_LIST.json")
        return self._code_items

    @property
    def debug_items(self) -> List[Dict[str, Any]]:
        """Lazily load debug/log items list."""
        if self._debug_items is None:
            self._debug_items = self._load_list("DEBUG_LOG_ITEMS_LIST.json")
        return self._debug_items

    def _load_list(self, filename: str) -> List[Dict[str, Any]]:
        """Load a JSON list file."""
        path = self._base_path / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_random_code_item(self) -> Dict[str, Any]:
        """Get a random code component item."""
        return self.rng.choice(self.code_items)

    def get_random_debug_item(self) -> Dict[str, Any]:
        """Get a random debug/log item."""
        return self.rng.choice(self.debug_items)

    def get_code_injection(self, include_header: bool = True) -> str:
        """
        Get a formatted code component suggestion for injection.

        Intended for: Code-focused pipeline, Step 2 (Solution Plan)

        Args:
            include_header: Whether to include the section header

        Returns:
            Formatted markdown suggestion text
        """
        item = self.get_random_code_item()

        text = ""
        if include_header:
            text += "## Random Seed Suggestion (Optional)\n\n"

        text += f"**Consider investigating: {item['name']}**\n\n"
        text += f"- **Location**: `{item['file_path']}`\n"
        text += f"- **Description**: {item['description']}\n"
        text += f"- **Potential issue**: {item['bug_hypothesis']}\n\n"
        text += "*This is a randomly-selected suggestion. If it seems relevant to the black screen issue, explore it. If not, feel free to ignore and proceed with your own analysis.*\n"

        return text

    def get_debug_injection(self, include_header: bool = True) -> str:
        """
        Get a formatted debug/log module suggestion for injection.

        Intended for: Error-focused pipeline, Step 2 (Solution Plan) and Step 4 (Hypotheses)

        Args:
            include_header: Whether to include the section header

        Returns:
            Formatted markdown suggestion text
        """
        item = self.get_random_debug_item()

        issues_list = ", ".join(item['detectable_issues'][:3])  # Limit to 3 for brevity

        text = ""
        if include_header:
            text += "## Random Seed Suggestion (Optional)\n\n"

        text += f"**Consider enabling logging for: {item['module']}**\n\n"
        text += f"- **Category**: {item['category']}\n"
        text += f"- **What it reveals**: {item['what_it_logs']}\n"
        text += f"- **Can detect**: {issues_list}\n"
        text += f"- **Useful when**: {item['when_useful']}\n\n"
        text += "*This is a randomly-selected suggestion. If this logging could help diagnose the black screen issue, consider enabling it. If not, feel free to ignore and proceed with your own analysis.*\n"

        return text

    def get_debate_injection(self,
                              pipeline: Literal["code", "error"],
                              include_header: bool = True) -> str:
        """
        Get a formatted suggestion for debate phase injection.

        Intended for: Debate rounds (both advocates)

        Args:
            pipeline: Which pipeline perspective ("code" or "error")
            include_header: Whether to include the section header

        Returns:
            Formatted markdown suggestion text
        """
        if pipeline == "code":
            item = self.get_random_code_item()
            item_name = item['name']
            brief = f"{item['description']} ({item['file_path']})"
            hypothesis = item['bug_hypothesis']
        else:
            item = self.get_random_debug_item()
            item_name = item['module']
            brief = f"{item['what_it_logs']} (Category: {item['category']})"
            hypothesis = f"Could reveal: {', '.join(item['detectable_issues'][:2])}"

        text = ""
        if include_header:
            text += "## Random Angle to Consider (Optional)\n\n"

        text += f"**Has either pipeline considered: {item_name}?**\n\n"
        text += f"- {brief}\n"
        text += f"- {hypothesis}\n\n"
        text += "*This is a randomly-selected prompt to potentially introduce fresh perspectives. If relevant to the current debate, consider incorporating it. If not, proceed with your argument.*\n"

        return text

    def get_hypothesis_injection(self, include_header: bool = True) -> str:
        """
        Get a formatted suggestion specifically for hypothesis formulation.

        Intended for: Error-focused pipeline, Step 4 (Hypotheses)

        Args:
            include_header: Whether to include the section header

        Returns:
            Formatted markdown suggestion text
        """
        item = self.get_random_debug_item()

        text = ""
        if include_header:
            text += "## Random Hypothesis Seed (Optional)\n\n"

        text += f"**Consider a hypothesis about: {item['category']}**\n\n"
        text += f"You could test whether the issue involves `{item['module']}`:\n"
        text += f"- This module logs: {item['what_it_logs']}\n"
        text += f"- It could reveal: {', '.join(item['detectable_issues'][:2])}\n\n"
        text += "*Use this as inspiration for a hypothesis if it seems relevant. Otherwise, formulate hypotheses based on your own analysis.*\n"

        return text

    def inject_into_prompt(self,
                           prompt_template: str,
                           injection_type: Literal["code", "debug", "debate_code", "debate_error", "hypothesis"],
                           marker: str = "{{RANDOM_INJECTION}}") -> str:
        """
        Inject a random suggestion into a prompt template.

        Args:
            prompt_template: The prompt template containing the marker
            injection_type: Type of injection to perform
            marker: The placeholder marker to replace

        Returns:
            Prompt with injection inserted
        """
        if injection_type == "code":
            injection = self.get_code_injection()
        elif injection_type == "debug":
            injection = self.get_debug_injection()
        elif injection_type == "debate_code":
            injection = self.get_debate_injection(pipeline="code")
        elif injection_type == "debate_error":
            injection = self.get_debate_injection(pipeline="error")
        elif injection_type == "hypothesis":
            injection = self.get_hypothesis_injection()
        else:
            raise ValueError(f"Unknown injection type: {injection_type}")

        return prompt_template.replace(marker, injection)

    def inject_after_step_header(self,
                                  prompt: str,
                                  step_header: str,
                                  injection_type: Literal["code", "debug", "hypothesis"]) -> str:
        """
        Inject suggestion after a specific step header in the prompt.

        This is useful when you don't want to modify the prompt template,
        but want to inject dynamically based on step headers.

        Args:
            prompt: The full prompt text
            step_header: The header to inject after (e.g., "## STEP 2: Create Solution Plan")
            injection_type: Type of injection to perform

        Returns:
            Prompt with injection inserted after the header
        """
        if injection_type == "code":
            injection = self.get_code_injection()
        elif injection_type == "debug":
            injection = self.get_debug_injection()
        elif injection_type == "hypothesis":
            injection = self.get_hypothesis_injection()
        else:
            raise ValueError(f"Unknown injection type: {injection_type}")

        # Find the header and inject after it
        if step_header in prompt:
            # Find the end of the header line
            header_pos = prompt.find(step_header)
            line_end = prompt.find('\n', header_pos)
            if line_end == -1:
                line_end = len(prompt)

            # Insert injection after header with proper spacing
            return (
                prompt[:line_end] +
                "\n\n" + injection + "\n" +
                prompt[line_end:]
            )

        # Header not found, return unchanged
        return prompt

    def get_injection_report(self) -> Dict[str, Any]:
        """
        Get a report of available items for injection.

        Useful for debugging or displaying statistics.

        Returns:
            Dictionary with counts and categories
        """
        debug_categories = {}
        for item in self.debug_items:
            cat = item['category']
            debug_categories[cat] = debug_categories.get(cat, 0) + 1

        return {
            "seed": self.seed,
            "code_components_count": len(self.code_items),
            "debug_items_count": len(self.debug_items),
            "debug_categories": debug_categories
        }


# Convenience function for quick single-use injection
def get_random_injection(
    injection_type: Literal["code", "debug", "debate_code", "debate_error", "hypothesis"],
    seed: Optional[int] = None
) -> str:
    """
    Convenience function to get a random injection without creating an injector instance.

    Args:
        injection_type: Type of injection
        seed: Optional random seed

    Returns:
        Formatted injection text
    """
    injector = RandomIdeaInjector(seed=seed)

    if injection_type == "code":
        return injector.get_code_injection()
    elif injection_type == "debug":
        return injector.get_debug_injection()
    elif injection_type == "debate_code":
        return injector.get_debate_injection(pipeline="code")
    elif injection_type == "debate_error":
        return injector.get_debate_injection(pipeline="error")
    elif injection_type == "hypothesis":
        return injector.get_hypothesis_injection()
    else:
        raise ValueError(f"Unknown injection type: {injection_type}")


if __name__ == "__main__":
    # Demo/test the injector
    print("=" * 60)
    print("Random Idea Injector Demo")
    print("=" * 60)

    injector = RandomIdeaInjector(seed=42)

    print("\n--- Injection Report ---")
    report = injector.get_injection_report()
    print(f"Code components: {report['code_components_count']}")
    print(f"Debug items: {report['debug_items_count']}")
    print(f"Debug categories: {report['debug_categories']}")

    print("\n--- Code Injection Example ---")
    print(injector.get_code_injection())

    print("\n--- Debug Injection Example ---")
    print(injector.get_debug_injection())

    print("\n--- Debate Injection (Code) Example ---")
    print(injector.get_debate_injection(pipeline="code"))

    print("\n--- Debate Injection (Error) Example ---")
    print(injector.get_debate_injection(pipeline="error"))

    print("\n--- Hypothesis Injection Example ---")
    print(injector.get_hypothesis_injection())
