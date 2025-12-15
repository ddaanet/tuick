#!/usr/bin/env bash -euo pipefail
# Generate test git repo with commits that produce diffs for testing

set -x  # Show commands as they execute

# Create temp directory for test repo
TEST_DIR=$(mktemp -d)/test_repo
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "Creating test repo in: $TEST_DIR"

# Initialize git repo
git init
git config user.email "test@example.com"
git config user.name "Test User"

# Test 1: Single closing paren at line start
echo "=== Test 1: Single closing paren ==="
cat > test1.py <<'EOF'
# Initial content
pass
EOF
git add test1.py
git commit -m "Initial commit for test1"

cat > test1.py <<'EOF'
# Initial content
def foo(
    x
)
pass
EOF
echo "Test 1 diff:"
git diff --unified=0 HEAD test1.py
echo

# Test 2: Closing bracket with indentation
git add test1.py && git commit -m "Add foo function"

cat > test2.py <<'EOF'
pass
EOF
git add test2.py
git commit -m "Initial commit for test2"

cat > test2.py <<'EOF'
items = [
    1, 2,
    3
    ]
pass
EOF
echo "Test 2 diff:"
git diff --unified=0 HEAD test2.py
echo

# Test 3: Non-Python file (should be ignored)
git add test2.py && git commit -m "Add items list"

cat > test3.md <<'EOF'
# Test
EOF
git add test3.md
git commit -m "Initial markdown"

cat > test3.md <<'EOF'
# Test
)
EOF
echo "Test 3 diff (should be ignored):"
git diff --unified=0 HEAD test3.md
echo

# Test 4: Multiple files
git add test3.md && git commit -m "Add paren to markdown"

cat > test4a.py <<'EOF'
pass
EOF
cat > test4b.py <<'EOF'
pass
EOF
git add test4a.py test4b.py
git commit -m "Initial test4 files"

cat > test4a.py <<'EOF'
foo(
)
pass
EOF
cat > test4b.py <<'EOF'
bar[
]
pass
EOF
echo "Test 4 diff (multiple files):"
git diff --unified=0 HEAD test4a.py test4b.py
echo

# Test 5: Multiple chunks with correct line numbers
git add test4a.py test4b.py && git commit -m "Add foo and bar"

cat > test5.py <<'EOF'
# Line 1
# Line 2
# Line 3
# Line 4
def existing():
    pass
# Line 8
# Line 9
# Line 10
# Line 11
# Line 12
# Line 13
# Line 14
# Line 15
# Line 16
# Line 17
# Line 18
# Line 19
def another():
    pass
EOF
git add test5.py
git commit -m "Initial test5"

cat > test5.py <<'EOF'
# Line 1
# Line 2
# Line 3
# Line 4
def existing():
foo(
)
    pass
# Line 8
# Line 9
# Line 10
# Line 11
# Line 12
# Line 13
# Line 14
# Line 15
# Line 16
# Line 17
# Line 18
# Line 19
def another():
bar(
)
    pass
EOF
echo "Test 5 diff (multiple chunks):"
git diff --unified=0 HEAD test5.py
echo

# Test 6: Delimiters not at line end (should be ignored)
git add test5.py && git commit -m "Add functions"

cat > test6.py <<'EOF'
pass
EOF
git add test6.py
git commit -m "Initial test6"

cat > test6.py <<'EOF'
) and more
    ]  # comment
pass
EOF
echo "Test 6 diff (delimiters not at end, should be ignored):"
git diff --unified=0 HEAD test6.py
echo

echo "Test repo created at: $TEST_DIR"
echo "To examine diffs manually:"
echo "  cd $TEST_DIR"
echo "  git log --oneline"
echo "  git show <commit>"
