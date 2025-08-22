import os
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import maya.cmds as cmds
import maya.api.OpenMaya as om
from functools import partial
from importlib import reload

from gg_autorig.utils import core
reload(core)


class PhotoButton(QtWidgets.QPushButton):
    def __init__(self, image_path, label_text, parent=None):
        super(PhotoButton, self).__init__(parent)

        # Setup main layout inside the button
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        pixmap = QtGui.QPixmap(image_path)
        pixmap = pixmap.scaled(32, 32, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        image_label = QtWidgets.QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(QtCore.Qt.AlignCenter)

        text_label = QtWidgets.QLabel(label_text)
        text_label.setAlignment(QtCore.Qt.AlignCenter)
        text_label.setWordWrap(False)

        layout.addWidget(image_label)
        layout.addWidget(text_label)

        self.setToolTip(label_text)

        # Let button shrink/expand nicely
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)

    def sizeHint(self):
        # Suggest a smaller default size (tight hitbox)
        return QtCore.QSize(60, 60)
    
    def on_clicked(self, name):
        om.MGlobal.displayInfo("Button clicked:", name)

class ControllerTab():

    def create_widgets(self):
        self.controllers_group = QtWidgets.QGroupBox("Controllers")

        self.controller_grid = QtWidgets.QGridLayout()
        self.controller_grid.setSpacing(5)
        self.controller_grid.setContentsMargins(5, 5, 5, 5)

        maya_icon_path = os.path.join(cmds.internalVar(upd=True), "icons", "cube.png")

        sample_names = [
            "L_armBuffer_CTL", "L_davicle_G", "L_fingerIndex_CTL",
            "L_fingerThumb_CTL", "L_heel_CTL", "L_legPv_CTL",
            "arrow_1", "arrow_2way", "arrow_4way", "circle_CTL"
        ]

        cols = 5
        for index, name in enumerate(sample_names):
            row = index // cols
            col = index % cols
            self.controller_grid.addWidget(PhotoButton(maya_icon_path, name), row, col)

        

        self.controller_settings = QtWidgets.QGroupBox("Controller Settings")
        self.controller_settings_layout = QtWidgets.QHBoxLayout()

        self.controller_size_label = QtWidgets.QLabel("Size:")
        self.controller_size_spinbox = QtWidgets.QSpinBox()
        self.controller_size_spinbox.setRange(1, 100)
        self.controller_size_spinbox.setValue(1)

        self.display_type_label = QtWidgets.QLabel("Display Type:")
        self.display_type_combobox = QtWidgets.QComboBox()
        self.display_type_combobox.addItems(["Normal", "Template", "Reference"])

        self.controller_name = QtWidgets.QRadioButton("Use controller name")
        self.custom_name = QtWidgets.QRadioButton("Use custom name")
        self.controller_name.setChecked(True)

        self.save_controller_name_label = QtWidgets.QLabel("Save Controller As:")
        self.save_controller_name_lineedit = QtWidgets.QLineEdit()

        self.controller_settings = QtWidgets.QGroupBox("Color Override")
        self.controller_settings_layout = QtWidgets.QHBoxLayout()



    def create_layout(self):
        self.create_widgets()

        self.controllers_group.setLayout(self.controller_grid)

        self.left_v_layout = QtWidgets.QVBoxLayout()
        radio_layout = QtWidgets.QHBoxLayout()
        radio_layout.addWidget(self.controller_name)
        radio_layout.addWidget(self.custom_name)
        self.left_v_layout.addLayout(radio_layout)
        controller_name_layout = QtWidgets.QHBoxLayout()
        controller_name_layout.addWidget(self.save_controller_name_label)
        controller_name_layout.addWidget(self.save_controller_name_lineedit)

        self.left_v_layout.addLayout(controller_name_layout)

        self.right_v_layout = QtWidgets.QVBoxLayout()
        # Controller Size layout
        size_layout = QtWidgets.QHBoxLayout()
        size_layout.addWidget(self.controller_size_label)
        size_layout.addWidget(self.controller_size_spinbox)
        self.right_v_layout.addLayout(size_layout)

        # Display Type layout
        display_type_layout = QtWidgets.QHBoxLayout()
        display_type_layout.addWidget(self.display_type_label)
        display_type_layout.addWidget(self.display_type_combobox)
        self.right_v_layout.addLayout(display_type_layout)

        self.controller_h_layout = QtWidgets.QHBoxLayout()
        self.controller_h_layout.addLayout(self.left_v_layout)
        self.controller_h_layout.addLayout(self.right_v_layout)

        self.controller_settings_layout.addLayout(self.controller_h_layout)

        self.controller_settings.setLayout(self.controller_settings_layout)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.controllers_group)
        main_layout.addWidget(self.controller_settings)
        main_layout.addStretch()

        return main_layout

    def create_connections(self):
       pass

  