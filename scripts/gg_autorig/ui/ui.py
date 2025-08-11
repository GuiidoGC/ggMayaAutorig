import os
import json
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from functools import partial

from gg_autorig.autorig import rig_builder_ui
from gg_autorig.utils.guides import guide_creation_ui
from gg_autorig.utils.guides import guides_manager
from importlib import reload
reload(rig_builder_ui)
reload(guide_creation_ui)
reload(guides_manager)

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
        button.setToolTip(label_text)  # tooltip here
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
        self.preset_combo.addItems(["Custom", "Human", "Elephant", "Dragon"])
        self.custom_path_label = QtWidgets.QLabel("Custom Guides Path:")
        self.custom_path = QtWidgets.QLineEdit()
        self.custom_path.setPlaceholderText("Enter custom path")
        self.custom_path_button = QtWidgets.QPushButton("Browse...")

        self.build_rig_button = QtWidgets.QPushButton("Set Guides")

        # RIG TOOLS - Module Library

        self.module_library = QtWidgets.QGroupBox()
        self.module_library.setTitle("Module Library")

        self.module_list = QtWidgets.QListWidget()        
        self.module_list.addItems(["Arm Module", "Front Leg Module", "Leg Module", "Back Leg Module", "Spine Module", "Neck Module"])

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
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

        globalctrl = QtWidgets.QTreeWidgetItem(["C_masterWalk_CTL"])
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

        self.build_guides = QtWidgets.QPushButton("Build Guides")
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

        asset_layout = QtWidgets.QVBoxLayout()
        asset_layout.addLayout(name_layout)
        asset_layout.addLayout(preset_layout)
        asset_layout.addLayout(custom_path_layout)

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

        settings_layout = QtWidgets.QVBoxLayout()
        settings_layout.addWidget(self.module_name_settings, alignment=QtCore.Qt.AlignCenter)
        settings_layout.setSpacing(20)
        settings_layout.addLayout(twist_joints_layout)
        settings_layout.addLayout(side_layout)  
        settings_layout.addLayout(self.rig_type_layout)
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
        end_buttons_layout.addWidget(self.build_guides)
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
        self.custom_path_button.clicked.connect(self.browse_custom_path)
        self.load_guides_button.clicked.connect(self.load_guides)


    def build_rig(self):
        om.MGlobal.displayInfo("Building rig...")
        rig_builder_ui.make(asset_name=self.asset_name_input.text())

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
        else:
            self.rig_type_label.setVisible(False)
            self.biped_radio.setVisible(False)
            self.quadruped_radio.setVisible(False)

        om.MGlobal.displayInfo(f"Selected module: {self.selected_module}")

    def hierarchy_selected(self):
        if self.tree.selectedItems():
            self.module_list.clearSelection()

        selected_items = self.tree.selectedItems()
        selected_item = selected_items[0]
        selected_item_text = selected_item.text(0)
        if not selected_item_text == "C_masterWalk_CTL":
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

    def add_guides(self):

        all_modules = [self.module_list.item(i).text() for i in range(self.module_list.count())]

        if self.module_name_settings.text() in all_modules:
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

            module_name = self.module_name_settings.text()

            if self.custom_path.text():
                self.path = self.custom_path.text()
            elif self.preset_combo.currentText() != "Custom":
                if self.preset_combo.currentText() == "Human":
                    self.path = "body_template_"
                elif self.preset_combo.currentText() == "Elephant":
                    self.path = "elephant_"
                elif self.preset_combo.currentText() == "Dragon":
                    self.path = "dragon_"
            else:
                self.path = self.asset_name_input.text().lower() + "_"

            modules_map = {
                "Arm Module": guide_creation_ui.ArmGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), file_name=self.path),    
                "Front Leg Module": guide_creation_ui.FrontLegGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), file_name=self.path),
                "Leg Module": guide_creation_ui.LegGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), file_name=self.path),
                "Back Leg Module": guide_creation_ui.BackLegGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), file_name=self.path),
                "Spine Module": guide_creation_ui.SpineGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), type=self.rig_type_group.checkedButton().text().lower(), file_name=self.path),
                "Neck Module": guide_creation_ui.NeckGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), type=self.rig_type_group.checkedButton().text().lower(), file_name=self.path),
            }

            if module_name in modules_map:
                guide = modules_map[module_name]
                self.guides = guide.create_guides(guides_trn, buffers_trn)
                self.end_guides.append(self.guides)
                om.MGlobal.displayInfo(f"Created guides for {module_name}: {self.guides}")

                # Add guides to the hierarchy tree
                parent_item = None
                for i, guide in enumerate(self.guides):
                    item = QtWidgets.QTreeWidgetItem([guide])
                    if i == 0:
                        # Parent first guide to masterWalk
                        master_items = self.tree.findItems("C_masterWalk_CTL", QtCore.Qt.MatchExactly)
                        if master_items:
                            master_items[0].addChild(item)
                        else:
                            self.tree.addTopLevelItem(item)
                        parent_item = item
                    else:
                        # Parent subsequent guides to previous guide (reverse chain)
                        if not "Settings" in guide:
                            parent_item.addChild(item)
                            parent_item = item
                # Optionally expand the masterWalk node
                master_items = self.tree.findItems("C_masterWalk_CTL", QtCore.Qt.MatchExactly)
                if master_items:
                    master_items[0].setExpanded(True)
                self.tree.setRootIsDecorated(True)

        else:
            for i, guide_grp in enumerate(self.end_guides):
                for guide in guide_grp:
                    if self.module_name_settings.text() == guide:
                        # Add and set jointTwist attribute
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

    def load_guides(self):

        if self.custom_path.text():
                self.path = self.custom_path.text()
        elif self.preset_combo.currentText() != "Custom":
            if self.preset_combo.currentText() == "Human":
                self.path = "body_template_"
            elif self.preset_combo.currentText() == "Elephant":
                self.path = "elephant_"
            elif self.preset_combo.currentText() == "Dragon":
                self.path = "dragon_"
        else:
            self.path = self.asset_name_input.text().lower() + "_"

        guide_creation_ui.load_guides(self.path)

        # modules_map = {
        #     "Arm Module": guide_creation_ui.ArmGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), file_name=self.path),    
        #     "Front Leg Module": guide_creation_ui.FrontLegGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), file_name=self.path),
        #     "Leg Module": guide_creation_ui.LegGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), file_name=self.path),
        #     "Back Leg Module": guide_creation_ui.BackLegGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), file_name=self.path),
        #     "Spine Module": guide_creation_ui.SpineGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), type=self.rig_type_group.checkedButton().text().lower(), file_name=self.path),
        #     "Neck Module": guide_creation_ui.NeckGuideCreation(side=self.side_combo.currentText()[0], twist_joints=self.twist_input.value(), type=self.rig_type_group.checkedButton().text().lower(), file_name=self.path),
        # }

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

        file_name = self.asset_name_input.text()
        guides_manager.guides_export(file_name=file_name, skelTree=hierarchy)

    def browse_custom_path(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.ReadOnly
        default_dir = os.path.dirname(__file__).split("scripts")[0]
        file_filter = "Guides Files (*.guides)"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Guides File", default_dir, file_filter, options=options)
        if file_path:
            self.custom_path.setText(file_path)
       
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



