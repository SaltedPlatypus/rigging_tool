from maya import cmds

from Util import utils
import build


def generate_guides(guide_data):

    result = build.generate_guide_from_cache(guide_data)
    return result


def update_rig(generated_guides):

    for guide, value in generated_guides.items():
        build.build_skeleton(value)


class GuideSelectionWindow:
    def __init__(self, main_window, *guides):
        self.guides = guides
        self.main_window = main_window  # Reference to the main UI window
        self.selected_guides = []  # List to store selected guides
        self.create_ui()  # Initialize the UI

    def create_ui(self):
        # Create a new window
        if cmds.window("guideSelectionWindow", exists=True):
            cmds.deleteUI("guideSelectionWindow", window=True)

        self.window = cmds.window("guideSelectionWindow", title="Select Guides", widthHeight=(200, 200))
        cmds.columnLayout(adjustableColumn=True)

        # Add a list box with options for guides (add as needed)
        self.list_box = cmds.textScrollList("guideList", allowMultiSelection=True, height=100)

        # List of available guides, add more as needed
        for guide in self.guides:
            cmds.textScrollList(self.list_box, edit=True, append=guide)

        # Add the Generate button
        cmds.button(label="Generate", command=self.on_generate)

        # Show the window
        cmds.showWindow(self.window)

    def on_generate(self, *args):
        # Get the selected guides
        selected_items = cmds.textScrollList(self.list_box, query=True, selectItem=True) or []

        if selected_items:
            # Pass the selected guides as arguments to the read_definition function
            self.main_window.on_generate_guide_button_click(
                selected_items
            )

        # Close the window after generating
        cmds.deleteUI(self.window, window=True)


class GuideUI:
    def __init__(self):

        self.generated_guides = {}  # Store the result as an instance variable
        self.json = None
        self.guide_data = None
        self.bipedal_guides = ["arm", "leg", "spine"]

        self.open_definition()
        self.read_definition()
        self.prepare_scene()

        self.create_ui()

    def open_definition(self):
        new_json = utils.open_definition("guides")
        self.json = new_json

    def read_definition(self):
        guide_data = utils.read_definition(self.json,
                                           *self.bipedal_guides)  # test with more in template URGENT
        self.guide_data = guide_data

    def prepare_scene(self):
        build.prep_scene(self.guide_data)

    def on_generate_guide_button_click(self, selected_items):
        """
        When we click generate with highlighted guide(s) selected in UI, we check if the selected
        guides are part of our self.guide_data which is built from out self.bipedal_guide data.
        :param selected_items: selected_items are the guides selected from the UI.
        :return:
        """

        for guide in self.guide_data:  # for guide in our built guide_data
            for item in selected_items:  # for item in our selected UI guides
                if item in guide:  # get the item from UI guide and find in our guide_data from JSON.
                    generated_guides = generate_guides(guide)
                    if generated_guides:
                        self.generated_guides[item] = generated_guides

    def open_guide_selection_window(self, *args):
        # Open the guide selection window
        GuideSelectionWindow(self, *self.bipedal_guides)

    def create_ui(self):
        if cmds.window("guideUIWindow", exists=True):
            cmds.deleteUI("guideUIWindow", window=True)  # Close the window if it already exists

        cmds.window("guideUIWindow", title="Guide Generator", widthHeight=(300, 150))
        cmds.columnLayout(adjustableColumn=True)

        # Create the button to open the guide selection window
        cmds.button(label="Select Guides", command=lambda *args: self.open_guide_selection_window())

        # Create the button and link it to the function
        # cmds.button(label="Generate Arm Guide", command=self.on_generate_guide_button_click)

        # Update Rig Button
        try:
            cmds.button(label="Update Rig", command=lambda x: update_rig(self.generated_guides))
        except Exception as e:
            print("Generate Guides First!")

        cmds.showWindow("guideUIWindow")


def main():
    guide = GuideUI()

if __name__ == '__main__':
    main()