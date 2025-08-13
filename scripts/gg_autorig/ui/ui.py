import os
import json
from PySide2 import QtWidgets, QtCore, QtGui
from gg_autorig.utils import core
from shiboken2 import wrapInstance
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from functools import partial

from gg_autorig.autorig import rig_builder_ui
from gg_autorig.utils.guides import guide_creation_ui
from gg_autorig.utils.guides import guides_manager
from gg_autorig.utils import core
from importlib import reload
import re
reload(rig_builder_ui)
reload(guide_creation_ui)
reload(guides_manager)
reload(core)

def get_maya_win():
    win_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(win_ptr), QtWidgets.QMainWindow)


def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)

class PhotoButton(QtWidgets.QWidget):
    def __init__(self, image_path, label_text, parent=None):
        super(PhotoButton, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        pixmap = QtGui.QPixmap(image_path)
        pixmap = pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        image_label = QtWidgets.QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(QtCore.Qt.AlignCenter)

        text_label = QtWidgets.QLabel(label_text)
        text_label.setAlignment(QtCore.Qt.AlignCenter)
        text_label.setWordWrap(True)

        button = QtWidgets.QPushButton()
        button.setToolTip(label_text) 
        button.setLayout(QtWidgets.QVBoxLayout())
        button.layout().setSpacing(0)
        button.layout().setContentsMargins(0, 0, 0, 0)
        button.layout().addWidget(image_label)
        button.layout().addWidget(text_label)
        button.setFixedSize(80, 100)
        button.clicked.connect(lambda: self.on_clicked(label_text))

        layout.addWidget(button)

    def on_clicked(self, name):
        om.MGlobal.displayInfo("Button clicked:", name)

class GG_Toolbox(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    TOOL_NAME = "Toolbox"

    def __init__(self, parent=None):
        delete_workspace_control(self.TOOL_NAME + 'WorkspaceControl')

        super(GG_Toolbox, self).__init__(parent or get_maya_win())
        self.setObjectName(self.TOOL_NAME)
        self.setWindowTitle(self.TOOL_NAME)
        self.setMinimumSize(300, 700)

        self.json_path = os.path.join(os.path.dirname(__file__), "styleSheet.json")
        self.selected = []
        self.end_guides = []
        self.local_axis_value = False

        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.apply_stylesheet()

        self.preset_combo.setCurrentIndex(1)

    def create_widgets(self):
        self.tabs = QtWidgets.QTabWidget()

        self.autorig_tab = QtWidgets.QWidget()
        self.controller_center_tab = QtWidgets.QWidget()
        
        # RIG TOOLS - Asset Settings
        self.configurations = QtWidgets.QGroupBox()
        self.configurations.setTitle("Asset Settings")

        self.asset_name_label = QtWidgets.QLabel("Asset Name:")
        self.asset_name_input = QtWidgets.QLineEdit()
        self.asset_name_input.setPlaceholderText("Enter asset name")

        self.preset_label = QtWidgets.QLabel("Presets:")
        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.addItems(["Custom", "Human", "Elephant", "Dragon", "New"])
        self.custom_path_label = QtWidgets.QLabel("Custom Guides Path:")
        self.custom_path = QtWidgets.QLineEdit()
        self.custom_path.setPlaceholderText("Enter custom path")
        self.custom_path_button = QtWidgets.QPushButton("Browse...")

        self.custom_ctl_path = QtWidgets.QLabel("Custom Controller Path:")
        self.custom_ctl_path_input = QtWidgets.QLineEdit()
        self.custom_ctl_path_input.setPlaceholderText("Enter custom path")
        self.old_path_button = QtWidgets.QToolButton()
        self.old_path_button.setArrowType(QtCore.Qt.DownArrow)  # Arrow icon
        self.old_path_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.custom_ctl_path_button = QtWidgets.QPushButton("Browse...")


        self.build_rig_button = QtWidgets.QPushButton("Set Guides")

        # RIG TOOLS - Module Library

        self.module_library = QtWidgets.QGroupBox()
        self.module_library.setTitle("Module Library")

        self.module_list = QtWidgets.QListWidget()        
        self.module_list.addItems(["Arm Module", "Front Leg Module", "Leg Module", "Back Leg Module", "Spine Module", "Neck Module", "Hand Module"])

        self.extra_module_library = QtWidgets.QGroupBox()
        self.extra_module_library.setTitle("Extra Module Library")

        self.extra_module_list = QtWidgets.QListWidget()
        self.extra_module_list.addItems(["Variable FK", "Rivet Module"])

        # RIG TOOLS - Settings
        self.settings = QtWidgets.QGroupBox()
        self.settings.setTitle("Default Modules Settings")

        self.module_name_settings = QtWidgets.QLabel("Arm Module")
        self.twist_label = QtWidgets.QLabel("Twist Joints:")
        self.twist_input = QtWidgets.QDoubleSpinBox()
        self.twist_input.setDecimals(0)
        self.twist_input.setMinimum(0)
        self.twist_input.setMaximum(100)
        self.twist_input.setSingleStep(1)
        self.twist_input.setValue(5)

        self.controllers_num = QtWidgets.QLabel("Number of controllers:")
        self.controllers_num_input = QtWidgets.QDoubleSpinBox()
        self.controllers_num_input.setDecimals(0)
        self.controllers_num_input.setMinimum(1)
        self.controllers_num_input.setMaximum(100)
        self.controllers_num_input.setSingleStep(1)
        self.controllers_num_input.setValue(5)

        self.side_label = QtWidgets.QLabel("Side:")
        self.side_combo = QtWidgets.QComboBox()
        self.side_combo.addItems(["Left", "Right", "Center"])
        self.rig_type_label = QtWidgets.QLabel("Rig Type:")
        self.biped_radio = QtWidgets.QRadioButton("Biped")
        self.quadruped_radio = QtWidgets.QRadioButton("Quadruped")
        self.biped_radio.setChecked(True)



        self.rig_type_group = QtWidgets.QButtonGroup()
        self.rig_type_group.addButton(self.biped_radio)
        self.rig_type_group.addButton(self.quadruped_radio)

        self.add_guides_button = QtWidgets.QPushButton("Add Guides")

        # RIG TOOLS - Extra Modules Settings
        self.extraModules = QtWidgets.QGroupBox()
        self.extraModules.setTitle("Extra Modules Settings")

        self.extra_module_name_settings = QtWidgets.QLabel("Variable FK")
        self.extra_module_name_input = QtWidgets.QLineEdit()
        self.extra_module_name_input.setPlaceholderText("Enter module name")

        self.extra_side_label = QtWidgets.QLabel("Side:")
        self.extra_side_combo = QtWidgets.QComboBox()
        self.extra_side_combo.addItems(["Left", "Right", "Center"])

        self.add_extra_guides_button = QtWidgets.QPushButton("Add Extra Guides")

        # Rig TOOLS - Hierarchy
        self.hierarchy = QtWidgets.QGroupBox()
        self.hierarchy.setTitle("Hierarchy")
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setMinimumHeight(300)
        self.tree.setMinimumWidth(200)
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

        globalctrl = QtWidgets.QTreeWidgetItem(["C_root_GUIDE"])
        self.tree.addTopLevelItem(globalctrl)
        globalctrl.setExpanded(True)
        self.tree.setRootIsDecorated(True)

        self.save_guides_button = QtWidgets.QPushButton("Save Guides")
        self.load_guides_button = QtWidgets.QPushButton("Load Guides")

        # Bottom Buttons
        
        self.extra_buttons = QtWidgets.QGroupBox()

        self.local_rotation_axis = QtWidgets.QPushButton("LRA")
        self.local_rotation_axis.setObjectName("local_rotation_axis")
        self.cvs = QtWidgets.QPushButton("CVs")
        self.cvs.setObjectName("cvs")
        self.node_editor = QtWidgets.QPushButton("Node Editor")
        self.node_editor.setObjectName("node_editor")
        self.selection_handles = QtWidgets.QPushButton("SelHan")
        self.selection_handles.setObjectName("selection_handles")
        self.save_selection = QtWidgets.QPushButton("Save Sel")
        self.save_selection.setObjectName("save_selection")
        self.load_selection = QtWidgets.QPushButton("Load Sel")
        self.load_selection.setObjectName("load_selection")

        self.mirror_selected_guides = QtWidgets.QPushButton("Mirror Selected Guides")
        self.build_rig_button = QtWidgets.QPushButton("Build Rig")


        # === Controller Creator Tab Widgets ===
        self.controller_scroll_area = QtWidgets.QScrollArea()
        self.controller_scroll_area.setWidgetResizable(True)

        self.controller_container = QtWidgets.QWidget()
        self.controller_grid = QtWidgets.QGridLayout(self.controller_container)
        self.controller_grid.setSpacing(0)
        self.controller_grid.setContentsMargins(0, 0, 0, 0)

        self.controller_scroll_area.setWidget(self.controller_container)

        maya_icon_path = os.path.join(cmds.internalVar(upd=True), "icons", "cube.png")

        sample_names = [
            "L_armBuffer_CTL", "L_davicle_G", "L_fingerIndex_CTL",
            "L_fingerThumb_CTL", "L_heel_CTL", "L_legPv_CTL",
            "arrow_1", "arrow_2way", "arrow_4way", "circle_CTL"
        ]

        cols = 4
        for index, name in enumerate(sample_names):
            row = index // cols
            col = index % cols
            self.controller_grid.addWidget(PhotoButton(maya_icon_path, name), row, col)

    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        # Asset input section layout
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(self.asset_name_label)
        name_layout.addWidget(self.asset_name_input)

        preset_layout = QtWidgets.QHBoxLayout()
        preset_layout.addWidget(self.preset_label)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addWidget(self.build_rig_button)

        custom_path_layout = QtWidgets.QHBoxLayout()
        custom_path_layout.addWidget(self.custom_path_label)
        custom_path_layout.addWidget(self.custom_path)
        custom_path_layout.addWidget(self.custom_path_button)

        custom_ctl_path_layout = QtWidgets.QHBoxLayout()
        custom_ctl_path_layout.addWidget(self.custom_ctl_path)
        custom_ctl_path_layout.addWidget(self.custom_ctl_path_input)
        custom_ctl_path_layout.addWidget(self.custom_ctl_path_button)

        asset_layout = QtWidgets.QVBoxLayout()
        asset_layout.addLayout(name_layout)
        asset_layout.addLayout(preset_layout)
        asset_layout.addLayout(custom_path_layout)
        asset_layout.addLayout(custom_ctl_path_layout)

        module_layout = QtWidgets.QVBoxLayout()
        module_layout.addWidget(self.module_list)
        module_layout.addStretch()

        extra_modules_layout = QtWidgets.QVBoxLayout()
        extra_modules_layout.addWidget(self.extra_module_list)
        extra_modules_layout.addStretch()


        twist_joints_layout = QtWidgets.QHBoxLayout()
        twist_joints_layout.addWidget(self.twist_label)
        twist_joints_layout.addWidget(self.twist_input)

        side_layout = QtWidgets.QHBoxLayout()
        side_layout.addWidget(self.side_label)
        side_layout.addWidget(self.side_combo)

        self.rig_type_layout = QtWidgets.QHBoxLayout()
        self.rig_type_layout.addWidget(self.rig_type_label)
        self.rig_type_layout.addWidget(self.biped_radio)
        self.rig_type_layout.addWidget(self.quadruped_radio)

        controllers_quantity_h_layout = QtWidgets.QHBoxLayout()
        controllers_quantity_h_layout.addWidget(self.controllers_num)
        controllers_quantity_h_layout.addWidget(self.controllers_num_input)

        settings_layout = QtWidgets.QVBoxLayout()
        settings_layout.addWidget(self.module_name_settings, alignment=QtCore.Qt.AlignCenter)
        settings_layout.setSpacing(20)
        settings_layout.addLayout(twist_joints_layout)
        settings_layout.addLayout(side_layout)  
        settings_layout.addLayout(self.rig_type_layout)
        settings_layout.addLayout(controllers_quantity_h_layout)
        settings_layout.addStretch()
        settings_layout.addWidget(self.add_guides_button, alignment=QtCore.Qt.AlignCenter)
        settings_layout.addStretch()

        extra_layout = QtWidgets.QVBoxLayout()
        extra_layout.addWidget(self.extra_module_name_settings, alignment=QtCore.Qt.AlignCenter)
        extra_layout.setSpacing(20)
        extra_layout.addWidget(self.extra_module_name_input)

        extra_layout_name_layout = QtWidgets.QHBoxLayout()
        extra_layout_name_layout.addWidget(self.extra_side_label)
        extra_layout_name_layout.addWidget(self.extra_side_combo)

        extra_layout.addLayout(extra_layout_name_layout)
        extra_layout.addStretch()
        extra_layout.addWidget(self.add_extra_guides_button, alignment=QtCore.Qt.AlignCenter)
        extra_layout.addStretch()

        hierarchy_layout = QtWidgets.QVBoxLayout()
        hierarchy_layout.addWidget(self.tree)
        hierarchy_layout.addStretch()

        hierachy_buttons_layout = QtWidgets.QHBoxLayout()
        hierachy_buttons_layout.addWidget(self.save_guides_button)
        hierachy_buttons_layout.addWidget(self.load_guides_button)
        hierarchy_layout.addStretch()

        hierarchy_layout.addLayout(hierachy_buttons_layout)

        self.configurations.setLayout(asset_layout)
        self.module_library.setLayout(module_layout)
        self.extra_module_library.setLayout(extra_modules_layout)
        self.settings.setLayout(settings_layout)
        self.extraModules.setLayout(extra_layout)
        self.hierarchy.setLayout(hierarchy_layout)

        rig_settings_layout = QtWidgets.QHBoxLayout()
        modules_v_layout = QtWidgets.QVBoxLayout()
        modules_v_layout.addWidget(self.module_library)
        modules_v_layout.addWidget(self.extra_module_library)
        rig_settings_layout.addLayout(modules_v_layout)
        rig_settings_v_layout = QtWidgets.QVBoxLayout()

        rig_settings_v_layout.addWidget(self.settings)
        rig_settings_v_layout.addWidget(self.extraModules)

        rig_settings_layout.addLayout(rig_settings_v_layout)
        rig_settings_layout.addWidget(self.hierarchy)

        extra_buttons_layout = QtWidgets.QHBoxLayout()
        extra_buttons_layout.addWidget(self.local_rotation_axis)
        extra_buttons_layout.addWidget(self.cvs)
        extra_buttons_layout.addWidget(self.node_editor)
        extra_buttons_layout.addWidget(self.selection_handles)
        extra_buttons_layout.addWidget(self.save_selection)
        extra_buttons_layout.addWidget(self.load_selection)

        end_buttons_layout = QtWidgets.QHBoxLayout()
        end_buttons_layout.addWidget(self.mirror_selected_guides)
        end_buttons_layout.addWidget(self.build_rig_button)

        self.extra_buttons.setLayout(extra_buttons_layout)
        
        # AutoRig tab layout
        autorig_layout = QtWidgets.QVBoxLayout()
        autorig_layout.addWidget(self.configurations)
        autorig_layout.addLayout(rig_settings_layout)
        autorig_layout.addStretch()
        autorig_layout.addWidget(self.extra_buttons)
        autorig_layout.addLayout(end_buttons_layout)

        self.autorig_tab.setLayout(autorig_layout)

        # Add tabs
        self.tabs.addTab(self.autorig_tab, "RigTool")
        self.tabs.addTab(self.controller_center_tab, "Controller Creator")

        controller_layout = QtWidgets.QVBoxLayout()
        controller_layout.addWidget(self.controller_scroll_area)
        self.controller_center_tab.setLayout(controller_layout)

        main_layout.addWidget(self.tabs)

    def create_connections(self):
        self.build_rig_button.clicked.connect(self.build_rig)
        self.module_list.itemClicked.connect(self.module_library_selected)
        self.tree.itemClicked.connect(self.hierarchy_selected)
        self.add_guides_button.clicked.connect(self.add_guides)
        self.node_editor.clicked.connect(lambda: cmds.NodeEditorWindow())
        self.selection_handles.clicked.connect(self.toggle_display_handle)
        self.save_selection.clicked.connect(partial(self.selection, True))
        self.load_selection.clicked.connect(partial(self.selection, False))
        self.cvs.clicked.connect(self.displayCvs)
        self.local_rotation_axis.clicked.connect(self.local_axis)
        self.save_guides_button.clicked.connect(self.get_tree_hierarchy)
        self.custom_path_button.clicked.connect(partial(self.browse_custom_path, type="Guides"))
        self.custom_ctl_path_button.clicked.connect(partial(self.browse_custom_path, type="CTLS"))
        self.load_guides_button.clicked.connect(self.load_guides)
        self.preset_combo.currentIndexChanged.connect(self.combo_box_changed)
        self.mirror_selected_guides.clicked.connect(self.mirror_selected_guide)

    def build_rig(self):
        om.MGlobal.displayInfo("Building rig...")
        if self.custom_ctl_path.text():
            self.ctl_path = self.custom_ctl_path.text()
        rig_builder_ui.make(asset_name=self.asset_name_input.text())

    def mirror_selected_guide(self):

        selected_items = cmds.ls(selection=True)
        if not selected_items:
            om.MGlobal.displayWarning("No guides selected in outliner for mirroring.")
        if selected_items:
            for item in selected_items:
                if cmds.attributeQuery("moduleName", node=item, exists=True):
                    attr = cmds.attributeQuery("moduleName", node=item, listEnum=True)[0].split(":")[0]
                    guide_list = cmds.attributeQuery("guide_name", node=item, listEnum=True)[0].split(":")
                    side = item.split("_")[0]
                    type_name = None
                    joint_twist = None
                    foot_module = None
                    controller_number = None
                    original_module = f"{side}_{attr}_GUIDE"
                    try:
                        joint_twist = cmds.getAttr(f"{item}.jointTwist")
                    except Exception as e:
                        pass
                    try:
                        controller_number = cmds.getAttr(f"{item}.controllerNumber")
                    except Exception as e:
                        pass
                    try:
                        type_enum = cmds.attributeQuery("type", node=item, listEnum=True)[0]
                        type_value = cmds.getAttr(f"{item}.type")
                        type_name = type_enum.split(":")[type_value]
                        om.MGlobal.displayInfo(f"Type enum name: {type_name}")

                    except Exception as e:
                        pass

                    def split_camel_case(text):
                        return ' '.join(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', text))

                    try:
                        split_name = split_camel_case(attr).split(" ")
                        split_name = ' '.join([word.capitalize() for word in split_name])
                    except Exception as e:
                        split_name = attr.capitalize()

                    om.MGlobal.displayInfo(f"Split module name: {split_name}")


                    if split_name == "Foot":
                        item = item.split("_")[1]
                        foot_module = split_camel_case(item).split(" ")
                        if len(foot_module) == 2:
                            foot_module = "Leg"
                        else:
                            foot_module = f"{foot_module[0]} {foot_module[1]}"

                    if side in ("L", "R"):
                        side = "R" if side == "L" else "L"
                    elif side == "C":
                        om.MGlobal.displayError("Cannot mirror Center (C) side guides.")
                        return

                    mirrored_guides = self.add_guides(mirror=[split_name + " Module", side, joint_twist, type_name, controller_number, f"{foot_module} Module"])

                    for original, mirrored in zip(guide_list, mirrored_guides):
                        orig_pos = cmds.xform(original, q=True, ws=True, t=True)
                        flipped_pos = [orig_pos[0] * -1, orig_pos[1], orig_pos[2]]
                        cmds.xform(mirrored, ws=True, t=flipped_pos)

                    om.MGlobal.displayInfo(f"Mirrored {original_module} to {side}_{attr}_GUIDE")

                else:
                    om.MGlobal.displayWarning("Selected guide is not mirrorable.")
                    return


    def module_library_selected(self):
        self.selected_module = self.module_list.currentItem().text()
        self.module_name_settings.setText(self.selected_module)
        self.settings.setTitle("Default Modules Settings")

        if self.module_list.selectedItems():
            self.tree.clearSelection()

        if self.selected_module == "Neck Module" or self.selected_module == "Spine Module":
            self.rig_type_label.setVisible(True)
            self.biped_radio.setVisible(True)
            self.quadruped_radio.setVisible(True)
            self.controllers_num.setVisible(False)
            self.controllers_num_input.setVisible(False)
        elif self.selected_module == "Hand Module":
            self.rig_type_label.setVisible(False)
            self.biped_radio.setVisible(False)
            self.quadruped_radio.setVisible(False)
            self.twist_input.setVisible(False)
            self.twist_label.setVisible(False)
            self.controllers_num.setVisible(True)
            self.controllers_num_input.setVisible(True)
        
        else:
            self.rig_type_label.setVisible(False)
            self.biped_radio.setVisible(False)
            self.quadruped_radio.setVisible(False)
            self.controllers_num.setVisible(False)
            self.controllers_num_input.setVisible(False)

        om.MGlobal.displayInfo(f"Selected module: {self.selected_module}")

    def hierarchy_selected(self):
        if self.tree.selectedItems():
            self.module_list.clearSelection()

        selected_items = self.tree.selectedItems()
        selected_item = selected_items[0]
        selected_item_text = selected_item.text(0)
        if not selected_item_text == "C_root_GUIDE":
            self.module_name_settings.setText(selected_item_text)
            self.settings.setTitle("Created Modules Settings")

            if selected_item_text == "Neck Module" or selected_item_text == "Spine Module":
                self.rig_type_label.setVisible(True)
                self.biped_radio.setVisible(True)
                self.quadruped_radio.setVisible(True)
            else:
                self.rig_type_label.setVisible(False)
                self.biped_radio.setVisible(False)
                self.quadruped_radio.setVisible(False)

    def add_guides(self, mirror=False):

        all_modules = [self.module_list.item(i).text() for i in range(self.module_list.count())]

        if self.module_name_settings.text() in all_modules or mirror:
            om.MGlobal.displayInfo("Adding guides...")
            if not cmds.objExists("guides_GRP"):
                guides_trn = cmds.createNode("transform", name="guides_GRP", ss=True)
            else:
                guides_trn = "guides_GRP"
            if not cmds.objExists("buffers_GRP"):
                buffers_trn = cmds.createNode("transform", name="buffers_GRP", ss=True, parent=guides_trn)
            else:
                buffers_trn = "buffers_GRP"
                if cmds.listRelatives(buffers_trn, parent=True) != [guides_trn]:
                    cmds.parent(buffers_trn, guides_trn)

            cmds.setAttr(f"{buffers_trn}.hiddenInOutliner ", True)

            module_name = mirror[0] if mirror else self.module_name_settings.text()

            side = mirror[1] if mirror else self.side_combo.currentText()[0]
            twist_joints = mirror[2] if mirror else self.twist_input.value()
            type = mirror[3] if mirror else self.rig_type_group.checkedButton().text().lower()
            controller_number = mirror[4] if mirror else self.controllers_num_input.value()

            limb_attr = mirror[5] if mirror else module_name

            limb_name = "foot" if limb_attr == "Leg Module" else limb_attr.split(" ")[0].lower() + "Leg"

            modules_map = {
                "Arm Module": guide_creation_ui.ArmGuideCreation(side=side, twist_joints=twist_joints),
                "Front Leg Module": guide_creation_ui.FrontLegGuideCreation(side=side, twist_joints=twist_joints),
                "Leg Module": guide_creation_ui.LegGuideCreation(side=side, twist_joints=twist_joints),
                "Back Leg Module": guide_creation_ui.BackLegGuideCreation(side=side, twist_joints=twist_joints),
                "Spine Module": guide_creation_ui.SpineGuideCreation(side=side, twist_joints=twist_joints, type=type),
                "Neck Module": guide_creation_ui.NeckGuideCreation(side=side, twist_joints=twist_joints, type=type),
                "Hand Module": guide_creation_ui.HandGuideCreation(side=side, controller_number=controller_number)
            }

            if mirror and mirror[0] == "Foot Module":
                    a = guide_creation_ui.FootGuideCreation(side=side, limb_name=limb_name)
                    self.guides = a.create_guides(guides_trn, buffers_trn)
                    return self.guides

            if module_name in modules_map:
                guide = modules_map[module_name]
                self.guides = guide.create_guides(guides_trn, buffers_trn)
                self.end_guides.append(self.guides)
                if "Leg" in module_name and not mirror:

                    guide_creation_ui.FootGuideCreation(side=side, limb_name=limb_name).create_guides(guides_trn, buffers_trn)

                parent_item = None

                words = module_name.replace(" Module", "").split()
                if words:
                    name = words[0].lower() + ''.join(w.capitalize() for w in words[1:])
                else:
                    name = module_name.replace(" Module", "").lower()

                item = QtWidgets.QTreeWidgetItem([f"{side}_{name}_GUIDE"])

                master_items = self.tree.findItems("C_root_GUIDE", QtCore.Qt.MatchExactly)
                if master_items:
                    master_items[0].addChild(item)
                if name == "spine":

                    hip_item = QtWidgets.QTreeWidgetItem([f"{side}_localHip_GUIDE"])
                    item.addChild(hip_item)

                self.tree.setRootIsDecorated(True)

                if mirror:
                    return self.guides

        else:
            for i, guide_grp in enumerate(self.end_guides):
                for guide in guide_grp:
                    if self.module_name_settings.text() == guide:
                        if cmds.attributeQuery("jointTwist", node=guide_grp[0], exists=True):
                            cmds.setAttr(f"{guide_grp[0]}.jointTwist", self.twist_input.value())
                        if cmds.attributeQuery("type", node=guide_grp[0], exists=True):
                            cmds.setAttr(f"{guide_grp[0]}.type", self.rig_type_group.checkedButton().text().lower())
                        
                        side_map = {"Left": "L", "Right": "R", "Center": "C"}
                        side = side_map.get(self.side_combo.currentText(), self.side_combo.currentText()[0])
                        for z, guide in enumerate(guide_grp):
                            side_name = guide.split("_")[0]
                            
                            if side_name != side:
                                renamed = cmds.rename(guide, guide.replace(f"{side_name}_", f"{side}_"))
                                if self.module_name_settings.text() == guide:
                                    self.module_name_settings.setText(renamed)
                                color = {"L": 6, "R": 13}.get(side, 17)
                                cmds.setAttr(f"{renamed}.overrideColor", color)
                                tree_item = self.tree.findItems(guide, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                                if tree_item:
                                    tree_item[0].setText(0, renamed)
                                
                                self.end_guides[i][z] = renamed  

        
    
    def check_last_file(self, file_path, existance=False):

        if existance:
            if not os.path.isfile(file_path):
                om.MGlobal.displayError(f"File not found: {file_path}")
                return False
        else:
            base, ext = os.path.splitext(file_path)
            dir_path = os.path.dirname(file_path)
            filename = os.path.basename(base)

            # Find all files matching the pattern (e.g., elephant_01.guides, elephant_02.guides)
            pattern = re.compile(rf"^{re.escape(filename[:-2])}(\d{{2}}){re.escape(ext)}$")
            existing_files = []
            for f in os.listdir(dir_path):
                match = pattern.match(f)
                if match:
                    existing_files.append((int(match.group(1)), os.path.join(dir_path, f)))

            if not existing_files:
                return file_path

            # Sort by index
            existing_files.sort()
            # Find the highest index file
            max_idx, max_file = existing_files[-1]

            # Try next index
            next_idx = max_idx + 1
            next_file = os.path.join(dir_path, f"{filename[:-2]}{next_idx:02d}{ext}")
            if os.path.isfile(next_file):
                # If next file exists, keep going
                while os.path.isfile(next_file):
                    next_idx += 1
                    next_file = os.path.join(dir_path, f"{filename[:-2]}{next_idx:02d}{ext}")
                # Return the last existing file
                return os.path.join(dir_path, f"{filename[:-2]}{next_idx-1:02d}{ext}")
            else:
                # If next file does not exist, return the highest existing file
                return max_file


    def combo_box_changed(self):

        default_dir = os.path.dirname(__file__).split("scripts")[0]
        guides_path = os.path.join(default_dir, "guides")
        ctls_path = os.path.join(default_dir, "curves")

        if self.preset_combo.currentText() == "Custom":
            guides_path_end = self.custom_path.text()
            ctls_path_end = self.custom_ctl_path_input.text()

            guides_path_check = self.check_last_file(guides_path_end, existance=True)
            ctls_path_check = self.check_last_file(ctls_path_end, existance=True)

            if guides_path_check and ctls_path_check:
                core.DataManager.set_guide_data(guides_path_end)
                core.DataManager.set_ctls_data(ctls_path_end)

                om.MGlobal.displayInfo(f"Guides path set: {core.DataManager.get_guide_data()}")
                om.MGlobal.displayInfo(f"Controllers path set: {core.DataManager.get_ctls_data()}")
            else:
                om.MGlobal.displayError("One or more custom paths are invalid.")
            
            return

        elif self.preset_combo.currentText() == "Human":
            guides_path = os.path.join(guides_path,  "body_template_01.guides")
            ctls_path = os.path.join(ctls_path, "body_template_01.ctls")

        elif self.preset_combo.currentText() == "Elephant":
            guides_path = os.path.join(guides_path,  "elephant_01.guides")
            ctls_path = os.path.join(ctls_path, "elephant_01.ctls")

        elif self.preset_combo.currentText() == "Dragon":
            guides_path = os.path.join(guides_path,  "dragon_01.guides")
            ctls_path = os.path.join(ctls_path, "dragon_01.ctls")

        elif self.preset_combo.currentText() == "New":
            template_name = self.asset_name_input.text().lower() + "_01"
            guides_path = os.path.join(guides_path,  f"{template_name}.guides")
            ctls_path = os.path.join(ctls_path, f"{template_name}.ctls")

        guides_path_end = self.check_last_file(guides_path)
        ctls_path_end = self.check_last_file(ctls_path)

        # If the file doesn't exist, create it
        for path in [guides_path_end, ctls_path_end]:
            if not os.path.exists(path):
                try:
                    with open(path, "w") as f:
                        f.write("{}")
                    om.MGlobal.displayInfo(f"Created file: {path}")
                except Exception as e:
                    om.MGlobal.displayError(f"Could not create file {path}: {e}")

        core.DataManager.set_guide_data(guides_path_end)
        core.DataManager.set_ctls_data(ctls_path_end)

        om.MGlobal.displayInfo(f"Guides path set: {core.DataManager.get_guide_data()}")
        om.MGlobal.displayInfo(f"Controllers path set: {core.DataManager.get_ctls_data()}")

    def custom_guide_added(self):

        guide_creation_ui.load_guides()

    def custom_controller_added(self):

        guide_creation_ui.load_guides()

    def load_guides(self):

        guide_creation_ui.load_guides()

        final_path = core.init_template_file(ext=".guides", export=False)

        try:
            with open(final_path, "r") as infile:
                guides_data = json.load(infile)

        except Exception as e:
            om.MGlobal.displayError(f"Error loading guides data: {e}")

        skelTree = guides_data.get("hierarchy")
        self.tree.clear()
        def add_items(parent, data):
            for key, children in data.items():
                item = QtWidgets.QTreeWidgetItem([key])
                parent.addChild(item)
                for child in children:
                    if isinstance(child, dict):
                        add_items(item, child)
        self.tree.setHeaderHidden(True)
        for branch in skelTree:
            add_items(self.tree.invisibleRootItem(), branch)


    def toggle_display_handle(self):
        selected = cmds.ls(selection=True)
        if not selected:
            om.MGlobal.displayWarning("No objects selected to toggle Selection Handle.")
            return
        for obj in selected:
            display_handle = cmds.getAttr(f"{obj}.displayHandle")
            try:
                if display_handle:
                    cmds.setAttr(f"{obj}.displayHandle", 0)
                else:
                    cmds.setAttr(f"{obj}.displayHandle", 1)
            except Exception as e:
                om.MGlobal.displayError(f"Could not set Selection Handle for {obj}: {e}")

    def selection(self, save=True, *args):
        if save:
            self.selected = cmds.ls(selection=True)
            if self.selected:
                om.MGlobal.displayInfo("Selection saved.")
            else:
                om.MGlobal.displayWarning("No selection to save.")
            
        else:
            if self.selected:
                cmds.select(self.selected, add=True)
                om.MGlobal.displayInfo("Selection loaded.")
            else:
                om.MGlobal.displayWarning("No saved selection to load.")

    def displayCvs(self):
        selected = cmds.ls(selection=True)
        if not selected:
            om.MGlobal.displayWarning("No objects selected.")
            return
        shapes = []
        for obj in selected:
            obj_shapes = cmds.listRelatives(obj, shapes=True, type="nurbsCurve", fullPath=True) or []
            shapes.extend(obj_shapes)

        if not shapes:
            om.MGlobal.displayWarning("No NurbsCurve found in selected objects.")
            return
        
        for shape in shapes:
            try:
                cmds.setAttr(f"{shape}.dispCV", not cmds.getAttr(f"{shape}.dispCV"))
            except Exception as e:
                om.MGlobal.displayError(f"Could not toggle CV display for {shape}: {e}")

    def local_axis(self):

        objs = cmds.ls(selection=True) or cmds.ls()
        
        for item in objs:
            try:
                cmds.setAttr(item + ".displayLocalAxis", self.local_axis_value)
            except:
                pass

        om.MGlobal.displayInfo(f"Local axis {'enabled' if self.local_axis_value else 'disabled'} for {'selected objects' if cmds.ls(selection=True) else 'all objects in the scene'}")

        self.local_axis_value = not self.local_axis_value

    def get_tree_hierarchy(self):
        def traverse_tree(item):
            hierarchy = {item.text(0): []}
            for i in range(item.childCount()):
                child = item.child(i)
                hierarchy[item.text(0)].append(traverse_tree(child))
            return hierarchy

        hierarchy = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            hierarchy.append(traverse_tree(item))

        guides_manager.guides_export(skelTree=hierarchy)

    def browse_custom_path(self, type= "Guides"):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.ReadOnly
        default_dir = os.path.dirname(__file__).split("scripts")[0]
        file_filter = f"{type.capitalize()} Files (*.{type.lower()})"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, f"Select {type.capitalize()} File", default_dir, file_filter, options=options)
        if file_path:
            if type == "Guides":
                self.custom_path.setText(file_path)
                if self.preset_combo.currentText() == "Custom":
                    core.DataManager.set_guide_data(file_path)
                    om.MGlobal.displayInfo(f"Custom guides path set: {file_path}")
            elif type == "CTLS":
                self.custom_ctl_path_input.setText(file_path)
                if self.preset_combo.currentText() == "Custom":
                    core.DataManager.set_ctls_data(file_path)
                    om.MGlobal.displayInfo(f"Custom controllers path set: {file_path}")

    def apply_stylesheet(self):
        if not os.path.exists(self.json_path):
            om.MGlobal.displayWarning(f"Stylesheet not found: {self.json_path}")
            return

        try:
            with open(self.json_path, "r") as file:
                style_dict = json.load(file)

            style_sheet = ""
            for selector, props in style_dict.items():
                style_sheet += f"{selector} {{\n"
                for prop, val in props.items():
                    style_sheet += f"    {prop}: {val};\n"
                style_sheet += "}\n"
            self.setStyleSheet(style_sheet)
        except Exception as e:
            om.MGlobal.displayError(f"Failed to load stylesheet: {e}")



