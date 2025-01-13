from maya import cmds

from Util import utils
import build


def generate_guides(guide_data):

    result = build.generate_guide_from_cache(guide_data)

    return result

def update_rig(generated_guides):

    build.build_skeleton(generated_guides)


class GuideUI:
    def __init__(self):

        self.generated_guides = {}  # Store the result as an instance variable
        self.json = None
        self.guide_data = None

        self.open_definition()
        self.read_definition()
        self.prepare_scene()

        self.create_ui()

    def open_definition(self):
        new_json = utils.open_definition("guides")
        self.json = new_json

    def read_definition(self):
        guide_data = utils.read_definition(self.json, "arm")  # head
        self.guide_data = guide_data

    def prepare_scene(self):
        build.prep_scene(self.guide_data)

    def on_generate_guide_button_click(self, *args):
        generated_guides = generate_guides(self.guide_data[0])  # Store the result
        if generated_guides:
            self.generated_guides = generated_guides

    def create_ui(self):
        if cmds.window("guideUIWindow", exists=True):
            cmds.deleteUI("guideUIWindow", window=True)  # Close the window if it already exists

        cmds.window("guideUIWindow", title="Guide Generator", widthHeight=(300, 150))
        cmds.columnLayout(adjustableColumn=True)

        # Create the button and link it to the function
        cmds.button(label="Generate Arm Guide", command=self.on_generate_guide_button_click)

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