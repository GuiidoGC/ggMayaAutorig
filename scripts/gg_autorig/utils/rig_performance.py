import maya.cmds as cmds
import random

def getAverageEvaluationTime(n=99, range_size=20):
    for controller in cmds.ls(type="transform"):
        if "_CTL" in controller:
            cmds.currentTime(0)
            cmds.setKeyframe(controller)
            
            cmds.currentTime(n+1)
            for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                num = round(random.uniform(0, 100), 1)
                cmds.setKeyframe(f"{controller}.{attr}", v=num)
                try:
                    cmds.setAttr(f"{controller}.{attr}", num)
                except:
                    pass

            cmds.setKeyframe(controller)

    buffer_size = 100
    current_frame = int(cmds.currentTime(q=True))

    tmp = cmds.file(q=True, exn=True)
    out_path = tmp[:tmp.rfind(".")]

    version = cmds.about(mnv=True).replace(" ", "")
    product = cmds.about(p=True).replace(" ", "")

    out_file = f"{out_path}_{product}_{version}_.txt"
    cmds.profiler(b=buffer_size)
    average_duration = 0
    for i in range(n):
        frame = current_frame + 1 + i*range_size
        cmds.profiler(r=True)
        cmds.profiler(s=True)
        cmds.currentTime(frame)
        cmds.profiler(s=False)
        cmds.profiler(o=out_file)
        with open(out_file, 'r') as file_object:
            lines = file_object.readlines()
            comment_tag = None
            for line in lines:
                if comment_tag is None and " = EvaluationGraphExecution" in line:
                    comment_tag = f"{line[:line.find(' ')]}\t"
                if comment_tag is not None:
                    if comment_tag in line:
                        duration = int(line.split('\t')[4])
                        average_duration += duration
                        break
    average_duration /= n
    print(f"{average_duration=} micro seconds\nPure fps={(1000000/average_duration)}")
    cmds.currentTime(current_frame)


getAverageEvaluationTime()
