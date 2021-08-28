import tukaan


class MyApp(tukaan.App):
    def __init__(self, title="My nice little Tukaan app"):
        tukaan.App.__init__(self, title=title)

        self.position = "center"

        self.button = tukaan.Button(self, text="Button")
        # self.button.on_click = lambda: print("ok")
        self.label = tukaan.Label(self, text="Label")

        self.pack_widgets()

    def pack_widgets(self):
        self.button.pack()
        self.label.pack()


def main():
    app = MyApp()

    print("User last active", app.user_last_active, "seconds ago.")

    app.run()


if __name__ == "__main__":
    main()
