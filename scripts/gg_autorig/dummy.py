import maya.cmds as cmds

def parented_chain():

    joints = []

    obj =  cmds.ls(sl=True, type="joint")

    for joint in obj:
        cmds.select(clear=True)
        joint_env = cmds.createNode("joint", n=joint.replace("_JNT", "_ENV"))

        print(f"Creating environment joint: {joint_env}")

        if joints:

            cmds.parent(joint_env, joints[-1])

        joints.append(joint_env)    

    
    for i, joint in enumerate(joints):
         
        if i != 0:
            mult_matrix = cmds.createNode("multMatrix", n=joint.replace("_JNT", "_MMX"), ss=True)
            cmds.connectAttr(obj[i] + ".worldMatrix[0]", mult_matrix + ".matrixIn[0]", force=True)
            cmds.connectAttr(joints[i+1] + ".worldInverseMatrix[0]", mult_matrix + ".matrixIn[1]", force=True)
            cmds.connectAttr(mult_matrix + ".matrixSum", joint_env + ".offsetParentMatrix", force=True)

            for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                cmds.setAttr(joint_env + "." + attr, 0)

            

        else:
            cmds.connectAttr(obj[i] + ".worldMatrix[0]", joint + ".offsetParentMatrix", force=True)


parented_chain()