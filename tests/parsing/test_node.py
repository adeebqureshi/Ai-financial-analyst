from app.parsing.node import DocumentNode


def test_node():

    root = DocumentNode(
        level=0,
        title="Document",
    )

    child = DocumentNode(
        level=1,
        title="Revenue",
    )

    root.add_child(child)

    assert root.child_count == 1

    assert root.children[0].title == "Revenue"