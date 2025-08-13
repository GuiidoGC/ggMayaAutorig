#Python libraries import
from maya import cmds
from importlib import reload
import maya.api.OpenMaya as om
import math

# Local imports
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils.guides.guides_manager import guide_import
from gg_autorig.utils import data_export

reload(data_export)

class HandModule():
    """
    Class to create a hand module in a Maya rigging setup.
    This module handles the creation of hand joints, controllers, and various systems such as stretch, reverse, offset, squash, and volume preservation.
    """
    def __init__(self):
        """
        Initializes the HandModule class, setting up paths and data exporters.

        Args:
            self: Instance of the HandModule class.
        """
        
        self.data_exporter = data_export.DataExport()

        self.modules_grp = self.data_exporter.get_data("basic_structure", "modules_GRP")
        self.skel_grp = self.data_exporter.get_data("basic_structure", "skel_GRP")
        self.masterWalk_ctl = self.data_exporter.get_data("basic_structure", "masterWalk_CTL")
        self.guides_grp = self.data_exporter.get_data("basic_structure", "guides_GRP")


    def make(self, guide_name):
        """
        Creates the spine module, including the spine chain, controllers, and various systems.

        Args:
            self: Instance of the SpineModule class.
        """

        self.guide_name = guide_name
        self.side = guide_name.split("_")[0] 

        self.module_trn = cmds.createNode("transform", name=f"{self.side}_handModule_GRP", ss=True, parent=self.modules_grp)
        self.controllers_trn = cmds.createNode("transform", name=f"{self.side}_handControllers_GRP", ss=True, parent=self.masterWalk_ctl)
        self.skinning_trn = cmds.createNode("transform", name=f"{self.side}_handSkinning_GRP", ss=True, p=self.skel_grp)

        # pick_matrix = cmds.createNode("pickMatrix", name="C_spinePickMatrix_PMX", ss=True)
        # cmds.connectAttr(f"{self.masterWalk_ctl}.worldMatrix[0]", f"{pick_matrix}.inputMatrix")
        # cmds.connectAttr(f"{pick_matrix}.outputMatrix", f"{self.module_trn}.offsetParentMatrix")

        self.create_chain()

        # self.data_exporter.append_data(f"C_spineModule", 
        #                             {"skinning_transform": self.skinning_trn,
        #                             "body_ctl": self.body_ctl,
        #                             "local_hip_ctl": self.localHip_ctl,
        #                             "local_chest_ctl": self.localChest_ctl,
        #                             }
        #                           )

    def create_chain(self):
        """
        Creates the spine joint chain by importing guides and parenting the first joint to the module transform.

        Args:
            self: Instance of the SpineModule class.
        """
        
        self.guides = guide_import(self.guide_name, all_descendents=True, path=None)

        if cmds.attributeQuery("moduleName", node=self.guides[0], exists=True):
            self.enum_str = cmds.attributeQuery("moduleName", node=self.guides[0], listEnum=True)[0]
        cmds.addAttr(self.skinning_trn, longName="moduleName", attributeType="enum", enumName=self.enum_str, keyable=False)

        self.hand_attribute_ctl, self.hand_attribute_ctl_grp = controller_creator(
            name=self.guides[0].replace("_GUIDE", "Attributes"),
            suffixes=["GRP", "ANM"],
            lock=["scaleX", "scaleY", "scaleZ", "visibility"],
            ro=True,
        )
        cmds.parent(self.hand_attribute_ctl_grp[0], self.controllers_trn)

        childs = cmds.listRelatives(self.guides[0], children=True)
        for child in childs:
            guides_chain = [child]
            descendants = cmds.listRelatives(child, allDescendents=True) or []
            descendants.reverse()
            for desc in descendants:
                guides_chain.append(desc)
            ctls = []
            for i, guides in enumerate(guides_chain):
                name = guides.replace("_GUIDE", "") if not "End" in guides else guides.replace("_GUIDE", "Ik")
                ctl, ctl_grp = controller_creator(
                    name=name,
                    suffixes=["GRP", "OFF", "ANM"],
                    lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                    ro=True,
                )

                if not ctls:
                    cmds.connectAttr(f"{guides}.worldMatrix[0]", f"{ctl_grp[0]}.offsetParentMatrix")
                else:
                    mult_matrix = cmds.createNode("multMatrix", name=guides.replace("_GUIDE", "Offset_MMX"), ss=True)
                    cmds.connectAttr(f"{guides}.worldMatrix[0]", f"{mult_matrix}.matrixIn[0]")
                    cmds.connectAttr(f"{ctls[-1]}.offsetParentMatrix", f"{mult_matrix}.matrixIn[1]")
                    cmds.connectAttr(f"{mult_matrix}.matrixSum", f"{ctl_grp[0]}.offsetParentMatrix")
                cmds.parent(ctl_grp[0], self.controllers_trn if not ctls else ctls[-1])
               
                ctls.append(ctl)