# Makefile for building agent role files from source fragments

BUILD = uv run build.py

SRC_DIR = src
ROLES_DIR = roles

# Source fragments
CORE = $(SRC_DIR)/core.md
CORE_MIN = $(SRC_DIR)/core-minimal.md
PLANNING = $(SRC_DIR)/planning.md
CODE_STYLE = $(SRC_DIR)/code-style.md
TESTING = $(SRC_DIR)/testing.md
TESTING_DESIGN = $(SRC_DIR)/testing-design.md
QUALITY = $(SRC_DIR)/quality.md
GIT = $(SRC_DIR)/git.md
RETROSPECTIVE_RULES = $(SRC_DIR)/retrospective-rules.md

# Role definition fragments
ROLEDEF_HIGH = $(SRC_DIR)/role-definition-planner-high.md
ROLEDEF_DETAIL = $(SRC_DIR)/role-definition-planner-detail.md
ROLEDEF_CODER = $(SRC_DIR)/role-definition-coder.md
ROLEDEF_QUALITY = $(SRC_DIR)/role-definition-quality.md
ROLEDEF_QA_CODER = $(SRC_DIR)/role-definition-qa-coder.md
ROLEDEF_LINE = $(SRC_DIR)/role-definition-line-counter.md
ROLEDEF_RETRO = $(SRC_DIR)/role-definition-retrospective.md
ROLEDEF_COMMIT = $(SRC_DIR)/role-definition-commit.md

# Role files
HIGH_PLANNER = $(ROLES_DIR)/high-level-planner.md
DETAIL_PLANNER = $(ROLES_DIR)/detail-planner.md
CODER = $(ROLES_DIR)/coder.md
QUALITY_AGENT = $(ROLES_DIR)/quality-agent.md
QA_CODER = $(ROLES_DIR)/qa-coder.md
LINE_COUNTER = $(ROLES_DIR)/line-counter.md
RETROSPECTIVE = $(ROLES_DIR)/retrospective.md
COMMIT_AGENT = $(ROLES_DIR)/commit-agent.md

ROLES = $(HIGH_PLANNER) $(DETAIL_PLANNER) $(CODER) $(QUALITY_AGENT) \
        $(QA_CODER) $(LINE_COUNTER) $(RETROSPECTIVE) $(COMMIT_AGENT)

.PHONY: all clean check

all: $(ROLES)

check: format all
	uv run pymarkdown --config .pymarkdown.json scan $(SRC_DIR)
	uv run pymarkdown --config .pymarkdown.json scan $(ROLES_DIR)

format:
	uv run mdformat --wrap 80 --number $(SRC_DIR)/*.md



$(HIGH_PLANNER): $(ROLEDEF_HIGH) $(CORE) $(PLANNING)
	$(BUILD) $@ "High-Level Planner Agent" $^

$(DETAIL_PLANNER): $(ROLEDEF_DETAIL) $(CORE) $(PLANNING) $(CODE_STYLE) $(TESTING_DESIGN)
	$(BUILD) $@ "Detail Planner Agent" $^

$(CODER): $(ROLEDEF_CODER) $(CORE_MIN) $(TESTING)
	$(BUILD) $@ "Coder Agent" $^

$(QUALITY_AGENT): $(ROLEDEF_QUALITY) $(CORE) $(CODE_STYLE) $(QUALITY)
	$(BUILD) $@ "Quality Agent" $^

$(QA_CODER): $(ROLEDEF_QA_CODER) $(CORE_MIN)
	$(BUILD) $@ "QA Coder Agent" $^

$(LINE_COUNTER): $(ROLEDEF_LINE) $(CORE_MIN) $(CODE_STYLE)
	$(BUILD) $@ "Line Counter Agent" $^

$(RETROSPECTIVE): $(ROLEDEF_RETRO) $(CORE) $(RETROSPECTIVE_RULES)
	$(BUILD) $@ "Retrospective Agent" $^

$(COMMIT_AGENT): $(ROLEDEF_COMMIT) $(CORE) $(GIT)
	$(BUILD) $@ "Commit Agent" $^

clean:
	rm -f $(ROLES)
