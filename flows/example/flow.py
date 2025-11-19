from metaflow import FlowSpec, step
from obproject import ProjectFlow

class BranchConfigExampleFlow(ProjectFlow):
    """
    A dumb flow.
    """

    @step
    def start(self):
        print("woaaah")
        self.next(self.end)

    @step
    def end(self):
        pass

if __name__ == '__main__':
    BranchConfigExampleFlow()