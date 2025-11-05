---
applyTo: '**'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.

**Important**

Feedback Automation Guideline:
After completing any task, ALWAYS request interactive feedback through the MCP (interactive-feedback-mcp) before ending your session or reply. Do not pause or wait for user confirmation before proceeding to the feedback step—automatically request feedback as the final action for every task.

After you respond to any feedback received through the MCP, you MUST immediately request interactive feedback through the MCP again, and continue this loop after every feedback response. Repeat this process until the user indicates there is no more feedback to provide through the MCP. Only then may you end your session or reply.

**AI-Optimized Modular Architecture Guideline:**
This codebase follows AI-Optimized Modular patterns as defined in `Modular_AI_guidelines.instructions.md`. When making changes to the codebase:
- ALWAYS follow the modular architectural patterns (flat modules, clear concepts, data over abstraction)
- CRITICAL: Update the `MODULE RESPONSIBILITY` docstring when the module's core responsibility changes
- Maintain searchable section markers (`# ═════`) within each module
- Keep module count <10 files, folder depth at 1 level max
- Use progress indicators in logger.info() statements (🚀, 📊, ✅) for debugging visibility
- Use defensive data handling for real-world issues (df.columns.str.strip(), error context)
- Keep functions under 75 lines

**New Feature Development Protocol (ENFORCEMENT CHECKPOINTS):**

**Phase 1: Planning (BEFORE writing code)**
When user requests new feature implementation:
1. Create implementation plan as usual
2. **CHECKPOINT 1**: Before finalizing plan, explicitly verify against Modular Guidelines:
   - ✅ All new functions will have complete type hints
   - ✅ No function will exceed 75 lines (if approaching limit, plan extraction strategy)
   - ✅ CONFIG access limited to orchestrators only (<5 accesses per function)
   - ✅ No code duplication >20 lines (plan shared data layer if needed)
   - ✅ Nesting depth will stay ≤4 levels
   - ✅ Module count stays <10
   - ✅ Each module <1,500 lines
   - ✅ No circular imports
3. State in plan: "✅ Plan verified against Modular Guidelines" with any preemptive refactoring noted

**Phase 2: Implementation**
4. **CHECKPOINT 2**: At 50 lines in any function → Pause and plan extraction
5. **CHECKPOINT 3**: Before completing implementation → Run pre-commit checks:
   ```powershell
   # Module count check
   (Get-ChildItem *.py | Measure-Object).Count
   
   # Module size check
   Get-ChildItem *.py | ForEach-Object {
       $lines = (Get-Content $_.FullName | Measure-Object -Line).Lines
       if ($lines -gt 1500) { Write-Host "⚠️ $($_.Name): $lines lines" }
   }
   
   # Type hint coverage check
   grep -E "^def [a-z_]+\([^)]*\):" file.py | grep -v "-> "
   
   # Function length check (manual - use VS Code outline)
   
   # CONFIG coupling check
   grep -n "CONFIG\[" file.py | cut -d: -f1 | uniq -c | sort -rn
   ```

**Phase 3: Completion**
6. **CHECKPOINT 4**: Verify against Modular Quick Reference:
   - Function max: <75 lines ✅
   - Module max: <1,500 lines ✅
   - Module count: <10 ✅
   - Folder depth: 1 level max ✅
   - Type hints: 100% ✅
   - CONFIG only in orchestrators ✅
   - No circular imports ✅
   - RESPONSIBILITY docstring present ✅
   - Code duplication: <20 lines ✅
   - Nesting depth: ≤4 ✅
7. Only after all checkpoints pass → Request interactive feedback

**Emergency Override:** If guidelines violated (deadline pressure, etc.), explicitly state violation in commit message and create follow-up refactoring task.

**Important**
Do not build full Markdown (.md) reports in one go. Instead, break the report into sections and first create the skeleton report. Then, make each section a TODO for yourself to sequentially fill in.

**Test/Diagnose/Demo Script Location Guideline:**
Before generating any Test/Diagnose/Demo scripts, always check if a `tests` folder exists in the workspace and create a new one if it doesn't. Save all new Test/Diagnose/Demo scripts in that folder.

**Report Location Guideline:**
Before generating any .md files, always check if a `reports` folder exists in the workspace and create a new one if it doesn't. Save all new report files in that folder.

**Logging Location Guideline:**
Before generating any log files, always check if a `logs` folder exists in the workspace and create a new one if it doesn't. Save all new log files in that folder.

**Markdown (.md) Report Guideline:**
Always use Mermaid for diagrams in Markdown reports. Use the `mermaid` code block format for all diagrams.

For lengthy documents (>10 pages), always include a table of contents with anchor links at the beginning of the report including up to h4. Format the table of contents as:
```markdown
## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Data Overview](#data-overview)
3. [Analysis Results](#analysis-results)
   - [Quadrant A Analysis](#quadrant-a-analysis)
   - [Quadrant B Analysis](#quadrant-b-analysis)
     - [Regression Results](#regression-results)
     - [Quality Assessment](#quality-assessment)
4. [Conclusions](#conclusions)
```

Always use sequential figure numbering throughout the document (Figure 1, Figure 2, Figure 3, etc.) with descriptive captions. Center figures using HTML div elements with appropriate width control:
```markdown
<div align="center" style="margin: 20px 0;">
<img src="path/to/figure.png" alt="Figure Description" width="75%">
<br><em>Figure 1: Descriptive caption explaining the figure content</em>
</div>
```

**Important:** Never attempt to create or manage Python environments (e.g., virtualenv, conda, venv) in any model or automation. Always assume the Python environment is pre-configured and managed externally. Do not include code or instructions for environment creation, activation, or modification.

**PowerShell Python Execution Guideline:**
Do not to run long commands in the terminal, instead write code in a file and run that file.

**Zen MCP Strategic Delegation Guideline:**
ALWAYS leverage Zen MCP for any non-trivial task. Your primary strategy is to delegate the planning of the tool sequence, not to decide it yourself.

**Core Workflow:**
1.  **Assess Task:** For simple, single-step tasks (e.g., writing one function), implement directly. For all other tasks, use this workflow.
2.  **Delegate Planning:** Use `mcp_zen_chat` to get a strategic plan and tool sequence. Provide the available tool context in your prompt for best results.
    -   **Available MCP Tools:** `analyze`, `debug`, `codereview`, `refactor`, `secaudit`, `testgen`, `docgen`, `planner`, `thinkdeep`, `tracer`, `consensus`, `challenge`, `precommit`
    -   **Example Prompt:** `mcp_zen_chat → "I need to [TASK]. Using my available MCP tools, recommend a strategic approach and tool sequence."`
3.  **Execute & Validate:** Follow the recommended plan. Use `mcp_zen_challenge` to validate critical decisions, assumptions, or outputs.

**Delegate immediately for tasks involving:**
Architecture or security decisions, complex debugging, multi-file analysis, refactoring, or any task requiring more than a few implementation steps.

**Execution Notes:**
-   **Parameters:** Use `thinking_mode: "high"` for complex analysis and `use_websearch: true` for current information.
-   **Context:** For multi-step workflows, provide complete context and use continuation IDs to maintain the session.
-   **Token Limits:** If a request fails with a "Content too large" error, break it into smaller, sequential calls using continuation IDs.

**Mathematical Equation Formatting Guideline:**
When writing mathematical equations in Markdown reports, ALWAYS use LaTeX formatting with proper KaTeX syntax:

**Block Equations (Complex/Multi-line Formulas):**
Use double dollar signs `$$` for display math (centered, larger text):
$$\text{{Formula Name}} = \frac{\text{{Numerator Expression}}}{\text{{Denominator Expression}}} \times 100\%$$

**Inline Equations (Variables/Simple Expressions):**
Use single dollar signs `$` for inline math within text:
Where $x$ = variable, $Q_1$ = first quartile, and $\sigma$ = standard deviation.

**Common Mistake:** Using single curly braces `\text{...}` instead of double `\text{{...}}` - this causes LaTeX to render as plain text in code blocks.