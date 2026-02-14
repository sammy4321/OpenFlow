import rumps

class StatusBar(rumps.App):
    """
    Manages the macOS status bar menu for OpenFlow.
    """

    def __init__(self, controller):
        super().__init__("OpenFlow", icon="resources/icon.png")
        self.controller = controller

        self.menu = [
            rumps.separator,
            "Quit",
        ]

    @rumps.clicked("Quit")
    def quit(self, _):
        rumps.quit_application()
