from beets.plugins import BeetsPlugin


class FromRegs(BeetsPlugin):
    def __init__(self):
        super(FromRegs, self).__init__()
        self.register_listener("pluginload", self.loaded)

    def loaded(self):
        self._log.info("fromregs loaded!")
        self._log.info(self.config["test"].get())
