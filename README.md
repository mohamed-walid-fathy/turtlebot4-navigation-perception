# TurtleBot 4 Navigation and Perception

ROS 2 robotics project for **CCAS 5.6 – Robotics and Automation Design**, implementing mapping, localization, Navigation2-based navigation, and computer-vision-based multi-target approach using a TurtleBot 4.

The project was developed and tested on a real TurtleBot 4 in a laboratory environment. The lab was scanned manually using SLAM Toolbox, the resulting map was saved for later localization/navigation, and an OpenCV-based perception module was developed to detect and autonomously approach red and blue markers.

## Project Overview

The project consisted of three main tasks:

1. **Mapping and pre-mapped navigation**
   - Generate an occupancy-grid map using SLAM Toolbox.
   - Save the map as a ROS 2 `.pgm` + `.yaml` map.
   - Localize the TurtleBot 4 against the saved map.
   - Navigate to operator-selected goals using Navigation2.

2. **SLAM-based navigation**
   - Manually drive the robot while SLAM Toolbox builds the environment map in real time.
   - Visualize the generated map in RViz.
   - Save the resulting map for later use.

3. **Perception and multi-goal navigation**
   - Process OAK-D RGB camera data with OpenCV.
   - Detect red and blue markers using HSV color segmentation.
   - Estimate marker position using image moments.
   - Align the robot with the detected marker.
   - Approach the marker autonomously.
   - Announce the detected color using speech synthesis.
   - Continue until both colored targets have been visited.

## Hardware

- **TurtleBot 4**
- **Create3 mobile base**
- **OAK-D RGB camera**
- **RPLIDAR**
- Host PC running Ubuntu and ROS 2 Jazzy

## Software

- **ROS 2 Jazzy**
- **Navigation2 (Nav2)**
- **SLAM Toolbox**
- **RViz2**
- **OpenCV**
- **Python**

## Repository Structure

```text
.
├── approach_two_colours.py
├── Command_Sheet.txt
├── my_map.pgm
├── my_map.yaml
├── my_map.jpg
├── Navigating_the_lab.mp4
├── Obstacle_avoidance_while_navigating.mp4
├── vision.mp4
└── vision_2nd_perspective.mp4
```

| File | Description |
|---|---|
| `approach_two_colours.py` | OpenCV/ROS 2 node for autonomous red and blue marker detection and approach |
| `Command_Sheet.txt` | Commands and RViz configuration used during the experiments |
| `my_map.pgm` | Occupancy-grid map generated from the laboratory scan |
| `my_map.yaml` | ROS 2 metadata for loading the map |
| `my_map.jpg` | JPG visualization of the laboratory map for convenient viewing on GitHub |
| `Navigating_the_lab.mp4` | Physical demonstration of TurtleBot 4 navigation |
| `Obstacle_avoidance_while_navigating.mp4` | Demonstration of navigation and obstacle avoidance |
| `vision.mp4` | Physical/computer-vision demonstration |
| `vision_2nd_perspective.mp4` | **Computer-screen perspective** of the vision experiment |

## 1. Mapping

The laboratory was manually scanned using the TurtleBot 4 and **SLAM Toolbox**.

The SLAM system used LiDAR measurements to incrementally construct an occupancy-grid representation of the environment while the robot was driven through the lab.

The resulting map was saved as:

```text
my_map.pgm
my_map.yaml
```

The `.pgm` and `.yaml` files are retained because they are the ROS 2 map representation used for localization. `my_map.jpg` is included as a convenient visual representation for GitHub visitors.

### Launch SLAM

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_navigation slam.launch.py
```

The robot can then be manually driven through the environment using teleoperation:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

## 2. Pre-Mapped Navigation

After the laboratory map was generated, it was used for localization and navigation.

### Start Localization

```bash
source /opt/ros/jazzy/setup.bash

ros2 launch turtlebot4_navigation localization.launch.py \
    map:=/home/ubuntu/Mohamedwalid/my_map.yaml
```

### Start Navigation2

```bash
source /opt/ros/jazzy/setup.bash

ros2 launch turtlebot4_navigation nav2.launch.py
```

### Start RViz

```bash
source /opt/ros/jazzy/setup.bash

ros2 launch turtlebot4_viz view_navigation.launch.py
```

The robot was localized successfully within the saved map, after which navigation goals were selected in RViz using the **Nav2 Goal** tool.

### RViz Configuration

| Setting | Value |
|---|---|
| Fixed Frame | `map` |
| Map topic | `/map` |
| LaserScan topic | `/scan` |
| Robot description | `/robot_description` |
| Map durability | `transient local` |

When using RViz, use the **Nav2 Goal** tool rather than the standard `2D Goal Pose` tool.

## 3. SLAM-Based Navigation

SLAM-based navigation differs from pre-mapped navigation because the robot builds its map while estimating its position.

For this project, **passive SLAM** was implemented. The robot was manually driven through the environment while SLAM Toolbox continuously updated the occupancy-grid representation using LiDAR measurements.

The resulting map was visualized in RViz and subsequently saved for use with the localization and Navigation2 workflow.

### Pre-Mapped vs SLAM-Based Navigation

| Feature | Pre-Mapped Navigation | SLAM-Based Navigation |
|---|---|---|
| Map availability | Requires an existing map | No prior map required |
| Localization | Localizes against a saved map | Localizes while building the map |
| Computational load | Lower | Higher |
| Environment knowledge | Known beforehand | Learned dynamically |
| Project implementation | Saved map + Navigation2 | Passive SLAM mapping |

## 4. OAK-D Camera

The TurtleBot 4 OAK-D camera was launched through an SSH connection to the robot.

```bash
ssh ubuntu@192.168.1.108

source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_bringup oakd.launch.py
```

The camera stream used by the perception system is:

```text
/oakd/rgb/preview/image_raw/compressed
```

Compressed images were used instead of the raw RGB stream to reduce latency and improve responsiveness.

### Check Camera Rate

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic hz /oakd/rgb/preview/image_raw
```

### Restart a Frozen Camera

```bash
source /opt/ros/jazzy/setup.bash

pkill -f oakd
pkill -f component_container

ros2 launch turtlebot4_bringup oakd.launch.py
```

## 5. Perception and Multi-Goal Navigation

The perception module was implemented in Python using **ROS 2, OpenCV, and NumPy**.

The main node is:

```text
approach_two_colours.py
```

It subscribes to:

```text
/oakd/rgb/preview/image_raw/compressed
```

and publishes velocity commands to:

```text
/cmd_vel
```

The overall behavior is:

```text
             Start
               │
               ▼
       Search for target
               │
               ▼
     Detect red or blue
               │
               ▼
       Estimate centroid
               │
               ▼
      Align with target
               │
               ▼
        Move forward
               │
               ▼
     Close enough to target?
          │          │
         No         Yes
          │          │
          └───┐      ▼
              │    Stop
              │      │
              │      ▼
              │  Announce color
              │      │
              │      ▼
              │ Remove target
              │ from goal list
              │      │
              └──────┤
                     ▼
             More targets?
                │       │
               Yes      No
                │        │
                └──────► Finish
```

### HSV Color Detection

Camera frames are converted from BGR to HSV color space.

Two masks are generated:

- Red
- Blue

For red, two HSV ranges are used to account for the hue wrap-around:

```text
H = 0–15
H = 160–180
```

For blue:

```text
H = 90–140
```

A color region must contain more than the configured minimum number of pixels before it is considered a valid target.

### Target Position

The node counts the pixels in each color mask and selects the largest valid remaining target.

OpenCV image moments are then used to calculate the target centroid:

```text
target_x = m10 / m00
```

The target's horizontal position is compared with the center of the camera image.

### Approach Controller

The robot uses the horizontal centroid error to determine angular velocity.

If the target is significantly away from the image center, the robot rotates toward it.

Once the target is sufficiently centered, the robot moves forward.

The detected target area is then used as a practical estimate of distance. When the target occupies a sufficiently large region of the image, the robot stops.

The implementation uses:

```text
MIN_PIXELS  = 20
CLOSE_PIXELS = 3000
```

The angular controller is proportional to the horizontal image error and is limited to avoid excessive rotational velocity.

### Multi-Target Behavior

The node begins with:

```python
remaining_colors = ["BLUE", "RED"]
```

The detected remaining target does not have to be visited in a fixed order.

After reaching a target:

1. The robot stops.
2. The detected color is announced using `espeak`.
3. The target is removed from the remaining target list.
4. The robot waits for 3 seconds.
5. The robot resumes searching for the next target.

The task terminates after both colors have been successfully visited.

## Running the Perception Node

Activate the Python environment and source ROS 2:

```bash
source ~/yolo_ws/yolo_env/bin/activate
source /opt/ros/jazzy/setup.bash
cd ~/yolo_ws/scripts
python approach_two_colours.py
```

Make sure the OAK-D camera is running before starting the perception node.

## ROS 2 Topics

| Topic | Purpose |
|---|---|
| `/map` | Occupancy-grid map |
| `/scan` | RPLIDAR LaserScan data |
| `/robot_description` | Robot model description |
| `/oakd/rgb/preview/image_raw/compressed` | OAK-D compressed RGB stream |
| `/cmd_vel` | Velocity commands |
| `/clicked_point` | RViz clicked-point information |

## Demonstration Videos

### Navigation

**`Navigating_the_lab.mp4`**

Demonstrates TurtleBot 4 navigating through the laboratory using the navigation stack and the generated map.

### Obstacle Avoidance

**`Obstacle_avoidance_while_navigating.mp4`**

Demonstrates navigation behavior while the robot encounters and navigates around obstacles.

### Vision

**`vision.mp4`**

Demonstrates the robot's vision/perception behavior during the colored-marker task.

### Computer-Screen Perspective

**`vision_2nd_perspective.mp4`**

This is the **second perspective recorded from the computer screen**. It shows the software side of the vision experiment, including the computer/RViz-side view rather than only the physical robot.

## Challenges Encountered

Several practical issues were encountered during the project.

| Challenge | Resolution |
|---|---|
| Create3 system clock was incorrectly set to 2022, causing synchronization problems and preventing proper RViz visualization | Corrected the robot clock and restored synchronization |
| Initial TurtleBot 4 unit exhibited severe hardware instability | Replaced the unit with another robot |
| ROS 2/TurtleBot 4 dependencies were missing | Required packages and libraries were manually installed and verified |
| Robot performance degraded at low battery levels | Charging was required before major experiments |
| Long charging cycles and sharing the robot between teams reduced testing time | Testing was organized around available robot time |
| Raw RGB image streams introduced significant latency | Switched to compressed image streams |
| An earlier motion-control implementation did not reliably move the robot | Redesigned the controller to publish `TwistStamped` velocity commands directly |

## Results

The implemented system achieved the main project objectives:

- Laboratory environment mapped using SLAM Toolbox.
- Generated map saved for later use.
- TurtleBot 4 localized within the saved map.
- Navigation goals executed using Navigation2.
- Environment and robot state visualized through RViz.
- OAK-D camera integrated into the ROS 2 perception pipeline.
- Red and blue markers detected using OpenCV.
- Robot autonomously aligned with and approached detected targets.
- Multiple targets visited sequentially.
- Target colors identified and announced using speech synthesis.

## Lessons and Future Improvements

The project provided practical experience integrating:

- SLAM and occupancy-grid mapping
- Robot localization
- Navigation2
- ROS 2 communication and topic management
- LiDAR-based environment perception
- Camera-based perception
- Closed-loop visual control
- Real-robot debugging and system configuration

Potential future improvements include:

- Active SLAM exploration rather than passive/manual exploration.
- Tighter integration between Navigation2 and the perception-based target behavior.
- More robust color segmentation under changing lighting conditions.
- More accurate visual distance estimation.
- Improved recovery behavior when a target is temporarily lost.
- More advanced perception and target-selection strategies.

## Useful Commands

### Localization

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_navigation localization.launch.py \
    map:=/home/ubuntu/Mohamedwalid/my_map.yaml
```

### Navigation

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_navigation nav2.launch.py
```

### RViz

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

### Teleoperation

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

### Camera

```bash
ssh ubuntu@192.168.1.108
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_bringup oakd.launch.py
```

### Perception

```bash
source ~/yolo_ws/yolo_env/bin/activate
source /opt/ros/jazzy/setup.bash
cd ~/yolo_ws/scripts
python approach_two_colours.py
```

## Project Report

A detailed project report accompanies this repository and documents the methodology, implementation, testing, challenges, navigation comparison, and results.

## Author

**Mohamed Walid**  
**Course:** CCAS 5.6 – Robotics and Automation Design

