from metaflow import step
from obproject import ProjectFlow

class BranchConfigExampleFlow(ProjectFlow):
    """
    A dumb flow.
    """

    @step
    def start(self):
        print("how now, brown cow.")
        print("we are running in staging :/")
        self.next(self.end)

    @step
    def end(self):
        pass

if __name__ == '__main__':
    BranchConfigExampleFlow()