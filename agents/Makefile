# Makefile for building agent role files from source fragments

PYTHON = uv run
BUILD = $(PYTHON) build.py

SRC_DIR = src
ROLES_DIR = roles

# Source fragments
CORE = $(SRC_DIR)/core.md
CORE_MIN = $(SRC_DIR)/core-minimal.md
PLANNING = $(SRC_DIR)/planning.md
CODE_STYLE = $(SRC_DIR)/code-style.md
TESTING = $(SRC_DIR)/testing.md
QUALITY = $(SRC_DIR)/quality.md
GIT = $(SRC_DIR)/git.md

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

.PHONY: all clean

all: $(ROLES)

$(HIGH_PLANNER): $(CORE) $(PLANNING)
	$(BUILD) $@ "High-Level Planner Agent" $^

$(DETAIL_PLANNER): $(CORE) $(PLANNING) $(CODE_STYLE)
	$(BUILD) $@ "Detail Planner Agent" $^

$(CODER): $(CORE_MIN) $(TESTING)
	$(BUILD) $@ "Coder Agent" $^

$(QUALITY_AGENT): $(CORE) $(CODE_STYLE) $(QUALITY)
	$(BUILD) $@ "Quality Agent" $^

$(QA_CODER): $(CORE_MIN)
	$(BUILD) $@ "QA Coder Agent" $^

$(LINE_COUNTER): $(CORE_MIN) $(CODE_STYLE)
	$(BUILD) $@ "Line Counter Agent" $^

$(RETROSPECTIVE): $(CORE) $(GIT)
	$(BUILD) $@ "Retrospective Agent" $^

$(COMMIT_AGENT): $(CORE) $(GIT)
	$(BUILD) $@ "Commit Agent" $^

clean:
	rm -f $(ROLES)
