import os
import maya.cmds as cmds
from importlib import reload
from maya.api import OpenMaya as om

# def init_template_file(path=None, file_name = "test_", ext=".guides", export=True):

class DataManager:
    _ctls_data = None
    _guide_data = None

    @classmethod
    def set_ctls_data(cls, data):
        cls._ctls_data = data

    @classmethod
    def get_ctls_data(cls):
        return cls._ctls_data

    @classmethod
    def set_guide_data(cls, data):
        cls._guide_data = data

    @classmethod
    def get_guide_data(cls):
        return cls._guide_data


def init_template_file(ext=".guides", export=True):
    """
    Initializes the TEMPLATE_FILE variable.
    If a path is provided, it sets TEMPLATE_FILE to that path.
    Otherwise, it uses the default template file path.
    """

    if ext == ".guides":
        file_name = DataManager.get_guide_data()
    elif ext == ".ctls":
        file_name = DataManager.get_ctls_data()

    end_file_path = None


    if not os.path.isabs(file_name):
        folder= {".guides": "guides", ".ctls": "curves"}
        complete_path = os.path.realpath(__file__)
        relative_path = complete_path.split("\scripts")[0]
        guides_dir = os.path.join(relative_path, folder[ext])
        base_name = file_name
        # Find all files matching the pattern
        existing = [
            f for f in os.listdir(guides_dir)
            if f.startswith(base_name) and f.endswith(ext)
        ]
        max_num = 1
        for f in existing:
            try:
                num = int(f[len(base_name):len(base_name)+2])
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
        default_template = os.path.join(guides_dir, f"{base_name}{max_num:02d}{ext}")
    else:
        default_template = file_name
        base_name = os.path.splitext(file_name)[0]

    if export:
        if os.path.exists(default_template):
            result = cmds.confirmDialog(
                title='Template Exists',
                message=f'{default_template} already exists. Replace it?',
                button=['Replace', 'Add +1', 'Cancel'],
                defaultButton='Replace',
                cancelButton='Cancel',
                dismissString='Cancel'
            )
            if result == 'Replace':
                end_file_path = default_template
            elif result == 'Add +1':
                base, ext = os.path.splitext(default_template)
                i = 2
                while True:
                        new_template = f"{base[:-2]}{i:02d}{ext}"
                        if not os.path.exists(new_template):
                                end_file_path = new_template
                                break
                        i += 1
            elif result == 'Cancel':
                om.MGlobal.displayWarning("Template creation cancelled.")
                return None
            else:
                end_file_path = None
    else:
        end_file_path = default_template

    return end_file_path
