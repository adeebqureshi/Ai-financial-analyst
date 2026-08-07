from app.parsing.hierarchy import HierarchyBuilder


def test_hierarchy():

    text = """
# Revenue

## Products

## Services

# Risk Factors
"""

    builder = HierarchyBuilder()

    root = builder.build(text)

    assert root.child_count == 2

    assert root.children[0].title == "Revenue"

    assert root.children[1].title == "Risk Factors"

    assert root.children[0].child_count == 2