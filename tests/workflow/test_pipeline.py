from app.workflow.pipeline import WorkflowPipeline


def test_pipeline():

    pipeline = WorkflowPipeline()

    graph = pipeline.build()

    assert len(graph.nodes) == 5