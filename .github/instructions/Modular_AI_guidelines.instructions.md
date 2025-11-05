---
applyTo: '**'
---

# AI-Optimized Modular Architecture Guidelines

## 🎯 Core Philosophy
Modules replace sections, not functions. Each module is one cohesive concept. **Modularization is a necessary evil** - use minimally.

## 🧠 When to Modularize

**The Three Valid Reasons:**
1. **UI/Logic Separation** - Streamlit/Flask: Thin UI layer calls thick logic modules
2. **Independent Feature Domains** - Multiple plot types: One module per feature
3. **Code Duplication** - >20 lines duplicated in 3+ places: Extract to shared module

**If your reason isn't above, DON'T modularize.**

## 🗂️ Module Structure

### **Streamlit Application Pattern:**
```
app/
├── app.py                      # UI ONLY (widgets, layout, session state)
├── config.py                   # CONFIG dictionary
├── processing_[feature].py     # Feature monoliths (keep existing lines)
├── validation.py               # CSV validation (one concept)
├── packaging.py                # ZIP generation (one concept)
└── shared_utils.py             # ONLY if 3+ modules duplicate code
```

**Anti-Pattern:** ❌ Deep hierarchies (`core/processors/aline/`)

## 📏 Hard Limits

| Constraint | Limit | Why |
|------------|-------|-----|
| **Function Max** | 75 lines | AI comprehension (unchanged from monolith) |
| **Module Max** | 1,500 lines | Single context window |
| **Module Count** | <10 files | AI mental model |
| **Folder Depth** | 1 level max | Flat structure only |
| **Imports** | <5 non-stdlib | Dependency tracking |
| **Circular Imports** | 0 (absolute) | Breaks AI context |
| **Code Duplication** | <20 lines | Extract to shared module |

## 🔧 Core Patterns

### **1. Functions Over Classes**
Use standalone functions unless managing 5+ related state variables.

**Exception:** Streamlit session state wrapper (5+ `st.session_state` variables)

### **2. Configuration Architecture**
```python
# config.py - Single source of truth
CONFIG = {"processing": {...}, "output": {...}}

def get_default_config() -> Dict[str, Any]:
    import copy
    return copy.deepcopy(CONFIG)

# processing_aline.py - Orchestrator extracts, business logic uses primitives
def generate_aline_plots(input_files: Dict[str, Path], output_dir: Path, 
                         config: Dict[str, Any]) -> Dict[str, Any]:
    # Extract config values
    batch_size = config["processing"]["batch_size"]
    # Call business logic with primitives
    data = load_aline_data(input_files["classification"], batch_size)
    return {"plots": plots, "data": data}

def load_aline_data(path: Path, batch_size: int) -> pd.DataFrame:
    """Business logic: No CONFIG access."""
    return pd.read_csv(path, chunksize=batch_size)
```

### **3. Module Responsibility Docstring**
```python
"""
MODULE: processing_aline.py

RESPONSIBILITY:
    Generates A-line plots from geotechnical CSV data.

KEY INTERACTIONS:
    INPUT:  Dict[str, Path], output_dir: Path, config: Dict
    OUTPUT: Dict[str, Any] {"plots": List[Path], "data": pd.DataFrame}
    CONFIG: processing.batch_size, output.dpi

AI NAVIGATION MARKERS:
    Search: # ═════ PHASE [N]:
    Entry: generate_aline_plots()
"""
```

### **4. Streamlit Pattern: Thin UI, Thick Logic**
`app.py` = ONLY widgets/layout. Zero business logic. Delegates to processing modules.

## ⚠️ Anti-Patterns

1. **Premature Abstraction** - ❌ Abstract base classes, ✅ Simple functions
2. **Utility Dumping Ground** - ❌ `utils.py` with 50 functions, ✅ Focused modules
3. **Deep Hierarchies** - ❌ 4 levels deep, ✅ Flat structure
4. **Excessive Contracts** - ❌ TypedDict/Protocol, ✅ Explicit signatures

## ✅ Pre-Commit Checklist

- [ ] Module count <10
- [ ] No folders except `tests/`
- [ ] Each module <1,500 lines
- [ ] Each function <75 lines
- [ ] 100% type hints
- [ ] CONFIG only in orchestrators
- [ ] No circular imports
- [ ] RESPONSIBILITY docstring present
- [ ] Section markers (`# ═════`) present
- [ ] No duplication >20 lines

## 🎓 Summary: Monolith → Modular

| Monolith | Modular | Why |
|----------|---------|-----|
| Single file | Flat modules | AI loads entire module |
| Section markers | Module + section markers | Navigate within/across |
| CONFIG at top | `config.py` | Single source |
| Functions | Still functions | Classes only for state (5+) |
| <75 lines/function | <75 lines/function | Unchanged |
| Type hints 100% | Type hints 100% | Required for contracts |

**Core Insight:** Modularize by **concept** (UI/processing/validation), not **abstraction** (interfaces/hierarchies).

---

**END OF MODULAR GUIDELINES**
