"""Shared rig / camera constants and deformation for PoseWear expressions (ICT-FaceKit light model)."""
import numpy as np, math
W, H = 900, 1200
LENS = 85.0
PIVOT = (0.0, -2.5, 1.0)      # head centre (cm, ICT units), rotation pivot & camera target
CAM_DIST = 88.0
GRAY = 0.5
AMBIENT = 0.35
KEY_ENERGY = 2.2; KEY_ROT = (-35, 25, 0)     # fixed relative to camera
FILL_ENERGY = 0.6; FILL_ROT = (-10, -50, 0)
# materials kept (lashes, lacrimal, eye blend/occlusion hidden)
KEEP_MATS = {'M_Face', 'M_BackHead', 'M_GumsTongue', 'M_Teeth', 'M_ScleraLeft', 'M_IrisLeft', 'M_ScleraRight', 'M_IrisRight'}
ANGLES = {  # (yaw about Y, pitch about X) degrees applied to the head; camera fixed
    'front': (0, 0),
    'three_quarter': (-40, 0),   # face turned to viewer's left
    'side': (-90, 0),            # profile facing viewer's left
    'high': (0, 30),             # camera looks down from above
    'low': (0, -25),             # camera looks up from below
}
EYE_L = (21451, 23021); EYE_R = (23021, 24591)
IRIS_L = (22221, 23021); IRIS_R = (23791, 24591)
LOWER_LIP_INNER = 5517   # 68-landmark #66
UPPER_LIP_INNER = 5966   # #62? (used for mouth gap)

def angle_matrix(name):
    yaw, pitch = ANGLES[name]
    y, p = math.radians(yaw), math.radians(pitch)
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    return Rx @ Ry

def _rotx(a):
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])

def deform(base, deltas, names, weights):
    """weights: ARKit/ICT blendshape names in [0,1] plus custom: eyeRollUp (0-1 -> 35deg), tongueOut (0-1)."""
    V = base.copy()
    idx = {n: i for i, n in enumerate(names)}
    for k, w in weights.items():
        if k in idx and w:
            V += float(w) * deltas[idx[k]]
    roll = float(weights.get('eyeRollUp', 0))
    if roll:
        R = _rotx(-math.radians(35 * roll))
        for a, b in (EYE_L, EYE_R):
            c = V[a:b].mean(0)
            V[a:b] = (V[a:b] - c) @ R.T + c
    t = float(weights.get('tongueOut', 0))
    tinfo = None
    if t:
        lip = V[LOWER_LIP_INNER]
        L = 1.5 + 2.6 * t                    # protrusion length
        tilt = math.radians(50 + 15 * t)     # tongue droops down over the lower lip
        S = np.diag([1.75, 0.5, 2.9, 1.0])
        Rt = np.eye(4); Rt[:3, :3] = _rotx(tilt)
        T = np.eye(4); T[:3, 3] = lip + np.array([0, -0.3 - 0.6 * t, -2.4 + L * 0.55])
        tinfo = (T @ Rt @ S).tolist()
    return V, tinfo
