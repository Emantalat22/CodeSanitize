"""Common Intermediate Representation (CIR) for Language-Agnostic Static Analysis.

Provides a unified, language-independent AST structure for Python, JavaScript,
TypeScript, Java, C++, C, Go, Rust, and other supported programming languages.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.schemas import SupportedLanguage


class IRNodeType(str, Enum):
    """Categorization of universal AST intermediate representation nodes."""

    PROGRAM = "program"
    FUNCTION = "function"
    CLASS = "class"
    STRUCT = "struct"
    INTERFACE = "interface"
    IMPORT = "import"
    IF_BRANCH = "if_branch"
    LOOP = "loop"
    TRY_CATCH = "try_catch"
    WITH_BLOCK = "with_block"
    ASSIGNMENT = "assignment"
    CALL = "call"
    COMMENT = "comment"
    STATEMENT = "statement"


class IRParameter(BaseModel):
    """Function or method parameter representation."""

    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None


class IRComment(BaseModel):
    """Comment or docstring record."""

    text: str
    is_docstring: bool = False
    line_start: int = 1
    line_end: Optional[int] = None


class IRCall(BaseModel):
    """Function, method, or constructor invocation."""

    callee_name: str
    arguments_count: int = 0
    line_start: int = 1
    is_eval_or_exec: bool = False
    is_subprocess: bool = False
    is_shell_true: bool = False


class IRAssignment(BaseModel):
    """Variable declaration or assignment statement."""

    target_name: str
    is_declaration: bool = False
    line_start: int = 1


class IRControlFlow(BaseModel):
    """Branching, looping, or exception handling block."""

    kind: str  # "if", "for", "while", "try", "catch", "match", "with"
    line_start: int = 1
    nesting_depth: int = 1
    branch_count: int = 1


class IRFunction(BaseModel):
    """Unified function, method, or closure definition."""

    name: str
    parameters: List[IRParameter] = Field(default_factory=list)
    line_start: int = 1
    line_end: int = 1
    is_async: bool = False
    is_generator: bool = False
    docstring: Optional[str] = None
    statement_count: int = 0
    cyclomatic_complexity: int = 1
    max_nesting_depth: int = 1
    calls: List[IRCall] = Field(default_factory=list)


class IRClass(BaseModel):
    """Unified class, struct, trait, or interface definition."""

    name: str
    class_type: str = "class"  # "class", "struct", "interface", "trait"
    bases: List[str] = Field(default_factory=list)
    methods: List[IRFunction] = Field(default_factory=list)
    fields: List[str] = Field(default_factory=list)
    docstring: Optional[str] = None
    line_start: int = 1
    line_end: int = 1


class IRImport(BaseModel):
    """Module import, include, or use declaration."""

    module_name: str
    imported_symbols: List[str] = Field(default_factory=list)
    alias: Optional[str] = None
    is_relative: bool = False
    line_start: int = 1


class IRProgram(BaseModel):
    """Root container representing the analyzed source file across any language."""

    language: SupportedLanguage
    lines_of_code: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    functions: List[IRFunction] = Field(default_factory=list)
    classes: List[IRClass] = Field(default_factory=list)
    imports: List[IRImport] = Field(default_factory=list)
    control_flows: List[IRControlFlow] = Field(default_factory=list)
    assignments: List[IRAssignment] = Field(default_factory=list)
    calls: List[IRCall] = Field(default_factory=list)
    comments: List[IRComment] = Field(default_factory=list)
    total_cyclomatic_complexity: int = 1
    max_nesting_depth: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
