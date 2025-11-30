from metaflow import step, Config
from obproject import ProjectFlow


class BranchConfigExampleFlow(ProjectFlow):
    """
    Example flow demonstrating branch-specific configuration.

    The flow_config is resolved by obproject-deploy based on the
    [environments.<env>.flow_configs] section in obproject.toml.
    """

    flow_config = Config("special_config", default="configs/flow.json")

    @step
    def start(self):
        print(f"Message: {self.flow_config['message']}")
        print(f"Log level: {self.flow_config['log_level']}")
        print(f"Max retries: {self.flow_config['max_retries']}")
        self.next(self.end)

    @step
    def end(self):
        print("Flow complete!")


if __name__ == "__main__":
    BranchConfigExampleFlow()
