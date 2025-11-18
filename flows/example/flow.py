from metaflow import FlowSpec, step
from obproject import ProjectFlow

class BranchConfigExampleFlow(ProjectFlow):
    """
    A dumb flow.
    """

    @step
    def start(self):
        print("Example flow - start")
        self.next(self.end)

    @step
    def end(self):
        print("Example flow - end")

if __name__ == '__main__':
    BranchConfigExampleFlow()