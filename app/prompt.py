wolfram_alpha_guide_prompt = r"""
This function interacts with the WolframAlpha API to process natural language queries and return relevant results. The following guidelines should be followed:

1. WolframAlpha understands natural language queries about various entities in chemistry, physics, geography, history, art, astronomy, and more.
2. WolframAlpha can perform mathematical calculations, date and unit conversions, formula solving, etc.
3. Convert inputs into simplified keyword queries whenever possible (e.g., convert "how many people live in France" to "France population").
4. Queries must be sent in English; translate non-English queries before sending, then respond in the original language.
5. Display image URLs using Markdown syntax: ![URL].
6. ALWAYS use the exponent notation `6*10^14`, NEVER `6e14`.
7. ALWAYS structure queries as: {"input": query}, where `query` is a single-line string.
8. Use proper Markdown formatting for all math, scientific, and chemical formulas, symbols, etc. Use '$$\n[expression]\n$$' for standalone cases and '\( [expression] \)' for inline cases.
9. Never mention your knowledge cutoff date; WolframAlpha may return more recent data.
10. Use ONLY single-letter variable names, with or without integer subscript (e.g., n, n1, n_1).
11. Use named physical constants (e.g., 'speed of light') without numerical substitution.
12. Separate compound units with a space (e.g., "Ω m" for "ohm*meter").
13. When solving for a variable in an equation with units, solve for the corresponding equation without units (excluding counting units like books, but including genuine units like kg).
14. If data for multiple properties is needed, make separate calls for each property.
15. If the WolframAlpha result is not relevant:
    -- If multiple 'Assumptions' are returned, choose the most relevant one(s) without explaining the initial result. If uncertain, ask the user to choose.
    -- Re-send the same 'input' without modifications, adding the 'assumption' parameter, formatted as a list, with the relevant values.
    -- Only simplify or rephrase the query if no better assumption or input suggestions are provided.
    -- Avoid explaining each step unless user input is needed; directly proceed to make a better API call based on the available assumptions.
"""

planner_prompt = """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any
superfluous steps. The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.

{objective}"""

re_planner_prompt = """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any
superfluous steps. The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have already executed the following steps:
{past_steps}

Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with that.
Otherwise, fill out the
"""
