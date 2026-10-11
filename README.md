# FactoryFlow3D: Smart Factory Simulator

An interactive, real-time 3D industrial automation simulation game built from scratch using **Python** and **PyOpenGL**. 

FactoryFlow3D models an automated logistics ecosystem featuring a continuous production conveyor belt, an autonomous robotic arm powered by **trigonometric Inverse Kinematics (IK)**, a dynamic automated guided vehicle (AGV) pathing pipeline, and structured facility health mechanics.

---

## 🚀 Key Engineering & Technical Features

* **Analytical Inverse Kinematics (IK):** Features explicit multi-joint coordinate angle resolution via a geometric trigonometric solver to smoothly direct the arm tip to volatile product coordinates.
* **Decoupled Asynchronous State Processing:** Runs concurrent lifecycle state machines tracking moving items on the belt, the active arm operational loops (`home`, `pickup`, `lift`, `drop`, `release`), and continuous coordinate path-finding routines for the warehouse AGV.
* **Defensive Input Validation:** Implements safe string decoding exceptions within the graphics thread listener to avoid core runtime crashes across fluctuating OS keyboard-buffer behaviors.
* **Multi-View Orthographic Overlays:** Dynamically flips projection matrices to lay a flat, pixel-perfect 2D Heads-Up Display (HUD) smoothly over an active 3D camera viewing frustum.
* **Gamified Production Mechanics:** Includes variable difficulty models, structural factory health limits, dynamic cameras (Overview, Robotic Arm, and AGV Follow views), and system failure states (Conveyor Jams and AGV obstacles).

---

## 🎮 Simulation Controls

### 🔧 Robotic Arm (Manual Mode)
* `M` : Toggle between **AUTOMATIC** and **MANUAL** arm tracking systems
* `A` / `D` : Rotate Arm Base 
* `W` / `S` : Adjust Shoulder Pitch
* `Q` / `E` : Adjust Elbow Pitch
* `Z` / `X` : Adjust Wrist Pitch
* `G` : Action button to open/close Gripper or pick/place nearby package

### 🏭 Factory & Environment Management
* `1` / `2` / `3` : Set Shift Difficulty (**EASY** / **NORMAL** / **HARD**)
* `SPACEBAR` : Trigger Emergency Stop (freezes all active loops)
* `J` : Simulate / Clear mechanical conveyor belt package jams
* `B` : Toggle an environmental safety obstacle in the AGV corridor
* `O` : Manually inject a customer warehouse order request
* `R` : Full factory simulator reset

### 🎥 Camera System
* `C` / `Right-Click` : Cycle Camera Profile (**Overview** ➔ **Robotic Arm** ➔ **AGV Follow**)
* `ARROW KEYS` : Orbit and pan the camera perspective within the 3D grid layout

---

## 🛠️ Installation & Setup Prerequisites

Ensure you have a Python environment installed on your local computer. Then, install the required graphics wrapper packages via your command terminal:

```bash
pip install PyOpenGL PyOpenGL_accelerate
```

### Running the Simulator
Run the main script directly from your terminal:

```bash
python FactoryFlow3D.py
```

---

## 📈 Future Refactoring Roadmap
* **OOP Architecture Migration:** Transition from the single-script procedural global variables schema into structured entities (`class RobotArm`, `class ConveyorSystem`, `class AGVehicle`).
* **External Asset Configurations:** Decouple layout bounds and specific RGB matrix vectors into a lightweight `.json` config manifest.
