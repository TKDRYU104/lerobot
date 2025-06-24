# GitHub Issue Submission Guide

## How to Submit the Issue

### 1. Navigate to LeRobot Repository

Go to: https://github.com/huggingface/lerobot/issues

### 2. Create New Issue

- Click "New issue" button
- Choose "Bug report" template if available, or use blank issue

### 3. Copy and Paste Content

Copy the entire content from `github_issue_template.md` and paste it into the issue description.

### 4. Add Labels (if possible)

Suggested labels:

- `bug`
- `hardware`
- `so100`
- `teleoperation`

### 5. Title

Use: "SO-100 Follower: Severe wrist_roll motor instability causing unwanted rotation during teleoperation"

## Additional Files to Attach

### 1. Analysis Report

Attach: `analysis/baseline_analysis_report.md`

### 2. Log Data Sample

Consider attaching a small sample of log data showing the problem:

- `motor_logs/motor_log_20250617_154125.csv` (or a subset)

### 3. Visualization Graphs

If available, attach graphs from `analysis/results/` folder:

- `wrist_roll_time_series.png`
- `correlation_heatmap.png`
- `motor_values_time_series.png`

### 4. Solution Scripts

Mention that you have implemented several solution approaches:

- P coefficient reduction
- Deadzone filtering
- Complete disabling workaround
- Advanced filtering system

## Key Points to Emphasize

### 1. Quantitative Evidence

- 95.596 standard deviation (extremely high)
- 100% of data points showing large values
- 242 large changes in 7 minutes
- Strong correlation with elbow_flex (-0.253)

### 2. Systematic Investigation

- Multiple approaches tested
- Quantitative measurement of improvements
- Root cause analysis performed
- Hardware vs software factors considered

### 3. Impact on Community

- Affects SO-100 usability for teleoperation
- Impacts data collection for ML
- Systematic issue affecting the platform

### 4. Willingness to Collaborate

- Extensive data available for sharing
- Multiple solution approaches implemented
- Ready to test proposed fixes
- Can provide additional debugging information

## Expected Response

The LeRobot team will likely:

1. Ask for additional technical details
2. Request specific log files or data
3. Suggest hardware debugging steps
4. Propose configuration changes to test
5. Connect you with other SO-100 users

## Follow-up Actions

After submitting:

1. Monitor the issue for responses
2. Be ready to provide additional data
3. Test any suggested solutions
4. Report back with results
5. Help other users experiencing similar issues

This comprehensive issue report should help the LeRobot team understand and address the problem effectively.
