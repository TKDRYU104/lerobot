# SO-100 Follower: Severe wrist_roll motor instability causing unwanted rotation during teleoperation

## Problem Description

The SO-100 Follower robot arm experiences severe instability in the `wrist_roll` motor during teleoperation, causing unwanted and uncontrollable rotation that significantly impacts usability. The motor exhibits extreme sensitivity and appears to be completely out of control in the default configuration.

## Environment

- **Robot**: SO-100 Follower
- **LeRobot Version**: [Current version]
- **Hardware**: Feetech STS3215 servos
- **OS**: macOS
- **Python**: 3.10.4

## Quantitative Analysis

### Baseline Analysis (Default Configuration)

- **Data Collection**: 416.5 seconds, 24,894 data points
- **Standard Deviation**: **95.596** (extremely high)
- **Large Changes (>10.0)**: **242 occurrences**
- **Value Distribution**:
  - Small values (|x|<5.0): **0%**
  - Large values (|x|≥10.0): **100%** (completely uncontrolled)

### Motor Correlation Analysis

Strong correlations with other motors suggest cross-coupling issues:

1. **elbow_flex.pos**: -0.253 (negative correlation, highest impact)
2. **shoulder_lift.pos**: 0.203 (positive correlation)
3. **gripper.pos**: 0.167 (positive correlation)
4. **shoulder_pan.pos**: 0.124 (weak positive correlation)
5. **wrist_flex.pos**: 0.026 (minimal correlation)

### Trigger Pattern Analysis

When wrist_roll experiences large changes (242 instances), average changes in other motors:

- **elbow_flex.pos**: 1.970 (highest trigger)
- **wrist_flex.pos**: 2.092
- **shoulder_lift.pos**: 1.119
- **gripper.pos**: 0.585
- **shoulder_pan.pos**: 0.426

## Root Cause Investigation

### 1. Motor Configuration Issues

- Default P_Coefficient (16) appears too high for wrist_roll motor
- No deadzone filtering in default configuration
- Potential hardware-level noise or mechanical coupling

### 2. Cross-Motor Interference

- Strong negative correlation with elbow_flex suggests mechanical or electrical interference
- Movement of other motors triggers unwanted wrist_roll rotation

### 3. Control System Sensitivity

- Motor responds to minimal input changes
- No built-in filtering for noise or small movements

## Reproduction Steps

1. Set up SO-100 Follower with default configuration
2. Run teleoperation:
   ```bash
   python -m lerobot.teleoperate \
       --robot.type=so100_follower \
       --robot.port=/dev/tty.usbserial-130 \
       --robot.id=blue \
       --teleop.type=so100_leader \
       --teleop.port=/dev/tty.usbserial-110 \
       --teleop.id=blue
   ```
3. Move any other motor (especially elbow_flex)
4. Observe unwanted wrist_roll rotation

## Attempted Solutions and Results

### 1. P Coefficient Reduction

**Implementation**: Reduced wrist_roll P_Coefficient from 16 to 4
**Result**: Improved standard deviation from 95.596 to 59.976 (37.3% improvement)

### 2. Deadzone Filtering

**Implementation**: Added deadzone threshold (5.0) to ignore small changes
**Result**: Partial improvement but problem persists

### 3. Advanced Filtering System

**Implementation**: Created comprehensive filtering with:

- Moving average filter
- Gripper-linked filter
- Combined filtering modes
  **Result**: Reduced responsiveness but didn't eliminate core issue

### 4. Complete Disabling (Workaround)

**Implementation**: Force wrist_roll value to 0.0 at all times
**Result**: Eliminates problem but removes wrist_roll functionality

## Proposed Solutions

### Short-term (Workarounds)

1. **Lower P Coefficient**: Further reduce to 2 or 1
2. **Stronger Deadzone**: Increase threshold to 20.0+
3. **Motor Disabling**: Provide option to disable problematic motors

### Long-term (Root Cause Fixes)

1. **Hardware Investigation**: Check for:

   - Cable interference/noise
   - Mechanical coupling between joints
   - Motor calibration issues
   - Power supply stability

2. **Software Improvements**:

   - Adaptive filtering based on motor correlations
   - Cross-motor interference compensation
   - Better default configurations for SO-100

3. **Configuration Options**:
   - Motor-specific P/I/D coefficients
   - Built-in filtering options
   - Hardware-specific presets

## Additional Data Available

I have collected extensive analysis data including:

- Multiple log files with quantitative measurements
- Correlation analysis scripts and results
- Visualization graphs showing the problem
- Working implementations of various filtering approaches

## Impact

This issue severely impacts the usability of SO-100 Follower robots for:

- Teleoperation tasks
- Data collection for machine learning
- Precise manipulation requirements

The problem appears to be systemic rather than isolated to individual units, suggesting a configuration or design issue that affects the SO-100 platform generally.

## Request for Assistance

Given the complexity of this issue and its impact on SO-100 usability, I would appreciate:

1. Guidance on hardware-level debugging approaches
2. Insights from other SO-100 users experiencing similar issues
3. Potential firmware or configuration updates
4. Recommendations for permanent solutions

I'm happy to provide additional data, logs, or testing results to help resolve this issue.
