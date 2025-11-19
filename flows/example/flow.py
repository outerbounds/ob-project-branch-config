from metaflow import step
from obproject import ProjectFlow

class BranchConfigExampleFlow(ProjectFlow):
    """
    A dumb, stable flow.
    """

    @step
    def start(self):
        print("woaaah")
        print("surfin in the main branch aka --production namespace.")
        self.next(self.end)

    @step
    def end(self):
        pass

if __name__ == '__main__':
    BranchConfigExampleFlow()